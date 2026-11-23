## 6. Results

MolBench has had two versions, and this paper names them in one way throughout. The *first
version* is the benchmark as it was public from May 2026 until the present corpus replaced
it. At the time of its last run it had a corpus of {{mvs.n_tasks}} scene
tasks on {{mvs.n_structures}} structures, {{legacy_api.n_tasks}} hand-written call-list
tasks, and two graders that compared text (Section 4.5). Two of its runs are used in this
paper: one of the call-list tasks in July 2026, and one of the scene tasks in October 2026,
which we call the *pilot run*. The *present version* is the benchmark of Sections 3 and 4.

The only results that exist today come from the first version. They are kept apart from
everything else, in the box of Section 6.6. The path to a provider has also been tried on a
few tasks of the present version; this *provider pilot* is not a result, and its one table
is in SI Section S6.1. Sections 6.1 to 6.5 show the tables that the
final run will fill: their layout, captions and definitions are fixed, and the cells are
filled by script from the archive of the run. Figure 5 shows the layout of the result figure.
In this draft the tables with one row per model (Tables 6, 9a and 9b) show their first rows
only, and Table 7 is described but not drawn.

![**Figure 5. Layout of the result figure that the final run will fill (no data shown).** **A**: task success rate (the share of answers whose drawn state is exactly right) per model, strict, with 95% intervals, one plot per track. The two plots must not be compared with each other (Section 4.2); formats are compared in panel B only. **B**: for each model, its {{corpus.twins.n_with_target}} pairs that have a target score, by which side was right (at least 2 of its {{plan.samples}} answers target-right, that is, with a target score of exactly 1: the requested style on the requested atoms and on no others). **C**: valid answers only, so that the panel shows what is lost after an answer could be shown: task success rate and target score (how far the requested style is on the requested atoms and on no others; unrequested background is ignored) per category. A target score well above the task success rate means that the requested atoms were right and something else was not. Panel A is strict and panel C is valid-only, so the two must not be compared.](generated/fig_result_shapes.svg)

### 6.1 Models on both tracks

**Table 6. Scene track, main condition.** One row per model; † marks an optional model.
*Weights*: open if the weights of the model can be downloaded, closed if the model can be
used only through a provider's service. *Valid answers*: share of answers that parse and that
the viewer accepts. *Task success rate*: share of answers whose drawn state is exactly right.
*Target score*: how far the requested style is on the requested atoms and on no others (0 to
1; exactly 1 is *target-right*); unrequested background, such as a cartoon of the protein, is
ignored. *F1*: how much of the drawn state is right (0 to 1).
*Strict*: every answer counts, and an unshowable answer scores 0. *Valid-only*: the mean over
the model's valid answers, pooled. *All-{{plan.samples}} rate*: share of tasks on which all
{{plan.samples}} answers are exactly right. *Cost*: US dollars for all calls of the model in
this condition, at list price. Intervals (95%, structures resampled; Section 5.4) will be
given with each score. F1 valid-only is in the SI.

{{include:generated/table_final_leaderboard_scene.md|else:generated/shape_leaderboard.md}}

**Table 7. Call-list track, main condition.** Same columns and definitions as Table 6, except
that a *valid answer* is a JSON list that fits the call schema, and a schema-breaking call list
keeps, under *strict*, the scores it earns when replayed (Section 4.4).

{{include:generated/table_final_leaderboard_calls.md|PENDING: final run — the table for the call-list track, in the shape of Table 6}}

### 6.2 Categories

**Table 8. Scores by category and track**, mean over the models (the two scripts are left
out). *Structures*: the number of structures that the tasks of the row sit on, which is the
number of units resampled for its intervals. *Task success rate*, *target score* and *F1* as
in Table 6. *Strict*: every answer counts, and an unshowable answer scores 0. *Valid-only*:
the mean over valid answers, which shows the difficulty of a category once the format has been
written correctly. The two rows marked *of which* divide the answers of the name-resolution
category by the entry that the model chose; they are sets of answers, so they have no number
of tasks. Answers on the reference entry are graded on drawn state; answers on another
accepted entry are, with few exceptions, compared with the reference as written (the weaker
rule of Section 4.1).

{{include:generated/table_final_tiers.md|else:generated/shape_tiers.md}}

### 6.3 The same request in two formats

**Table 9. Paired comparison of the two formats.** For each model, its pairs (one request on
both tracks, same target atoms) are divided into four cells, in two tables. A side of a pair
is *right* when at least 2 of its {{plan.samples}} answers are right. *Table 9a* (primary): an
answer is right when it is target-right, that is, its target score is exactly 1: the
requested style is on the requested atoms and on no others, and unrequested background is
ignored. This is the same test in both formats. Table 9a covers the
{{corpus.twins.n_with_target}} pairs that have a target score; the other
{{corpus.twins.n_without_target}}, all follow-up pairs, have none (Sections 4.2 and 5.4) and
appear in Table 9b only. *Table 9b* (secondary): an answer is right
when it is a task success, that is, its whole drawn state is exactly right; this is not the
same test in the two formats (Section 4.2). Table 9b covers all {{corpus.n_twin_pairs}}
pairs. An unshowable answer is not right. The four count columns give the number of pairs right
on both sides, on one side only, or on neither. *McNemar p*: exact test that the two one-sided
counts are equal; a small value means that one format is harder for this model. The test
treats pairs as independent (Section 5.4). *Difference*: the number of pairs right in the
scene only minus the number right in the call list only, as a share of the pairs, with a 95%
interval (structures resampled). † marks an optional model.

{{include:generated/table_final_paired.md|else:generated/shape_paired.md}}

Where both formats demand the same knowledge, which is every category with pairs except the
clinical one, a pair that is target-right on one side only points to the format, and a pair
that is wrong on both sides is a candidate for an error of content. Clinical pairs must be
read differently. There a right call list does not show that the model knew the residue,
because the viewer can do the mapping (Section 3.4); "call list right, scene wrong" then
points to the mapping, not to the scene format. The counts without the clinical pairs are
the cleaner test of the formats.
⟦PENDING: final run — the same counts without the clinical pairs, and without the {{corpus.twins.need_hide_toggle}} pairs whose reference call list switches off part of the default view (Section 3.4); and, in the SI, the one-sided pairs divided by whether the side that was not right was unshowable⟧

### 6.4 Clinical variants

**Table 10. Clinical tasks on the scene track, grouped by whether copying the number is
right.** On this track the model must map the number itself. *Target score* (how far the
requested style is on the requested residue and on no other atoms, with unrequested
background ignored; 0 to 1; the primary score of this table) and *task success rate* (drawn
state exactly right), strict, mean over the models; SI Section S9 will give the first two
rows for each model. *With grounding pack*: the result of the
lookup, including the mapped residue, is appended to the request. The rows are two
groupings of the same {{clin.n}} tasks (Section 3.3.1, Table 2a). *Copying the number*: an
answer that uses the number printed in the variant name as the author residue number is right,
or wrong. *Offset*: the author number of the target residue differs from its UniProt number,
or does not. The *difference* row is planned comparison 7 of Section 5.4. *Matched tasks*:
the same variant, named in UniProt numbering, asked on a structure with an offset and on a
predicted structure without one ({{clin.n_offset_pairs_uniprot_name}} sets; descriptive
only; Section 3.3.1). In the helix and strand tasks the model
must also know where the entry records that helix or strand to begin and end; they are a
subset of the {{clin.n}} and are also reported apart.

{{include:generated/table_final_clinical.md|else:generated/shape_clinical.md}}

This table will answer the question of the Introduction: do models map the number in a
variant name, or copy it? Four patterns are possible in its first two rows. We predict none
of them.

1. *Copying.* The target score is high where copying is right and low where it is wrong.
2. *Mapping.* The target score is high in both rows.
3. *Always converting.* The target score is low where copying is right and high where it is
   wrong. A model may have learned that file numbers usually differ from UniProt numbers and
   change the number in every case, for example by subtracting the length of a signal
   peptide. On a structure that is numbered as the request is, this turns a right number into a
   wrong one.
4. *Neither.* The target score is low in both rows. The loss then lies elsewhere, for example
   in the chain identifier or in invalid answers, and the table does not decide between
   copying and mapping.

Only pattern 2 shows that a model knows how each structure is numbered; a habit of copying or
of converting is not enough. With the grounding pack, which states the mapped residue,
patterns 1 and 3 should both turn into pattern 2. The patterns are stated on the target
score, because the task success rate also falls when an answer adds unrequested context.

The patterns describe one model, and Table 10 gives a mean over models, in which a mixture
of copying and converting models could pass for pattern 4. The question is therefore answered
model by model: SI Section S9 will give the first two rows and their difference, with its
interval, for each model. "High" and "low" have no fixed threshold. A model shows pattern 1
when the interval of its difference (copying right minus copying wrong) lies above zero, and
pattern 3 when it lies below zero. Where the interval includes zero, pattern 2 or 4 is read
from the level of the two rows, which we report and do not classify by rule.
⟦PENDING: final run — the number of models under each pattern, from the per-model rows of SI Section S9⟧

### 6.5 Follow-up turns, requests with several right answers, and planned comparisons

Table 11 divides the follow-up turns by whether a change is needed, and Table 12 holds the
planned comparisons 1 to 6 of Section 5.4.

**Table 11. Follow-up turns and requests with several right answers.** *Task success rate*:
share of answers whose drawn state is exactly right (for a request with several right answers:
the drawn state equals any one of the accepted answers), strict, mean over the models.

{{include:generated/table_final_followup.md|else:generated/shape_followup.md}}

**Table 12. Planned comparisons 1 to 6 of Section 5.4.** Each row compares the task success rate (share of answers
whose drawn state is exactly right; strict, mean over the models) between two groups of tasks
or two conditions, with a 95% interval on the difference (structures resampled). *Set-aside
split*: the tasks on {{corpus.heldback.n_structures}} structures that no earlier release
used; they are public too (Section 3.6). *Main*: the
main condition. *JSON mode*: the provider's option that forces syntactically valid JSON. It is
run on the models that offer it ({{plan.n_json_mode_models}} of the {{plan.n_core_models}}
core models and each optional model that is run), with one answer per task, which is set
against the mean of the {{plan.samples}} main answers. *Grounding pack*: the result of an offline lookup,
including the mapped residue or the list of entries, appended to the request. *Format guide*: the text in
the system prompt that documents the answer format.

{{include:generated/table_final_robustness.md|else:generated/shape_robustness.md}}

⟦PENDING: final run — outcome counts per model (valid, unshowable by kind, schema-breaking, cut off), the repaired scores, F1 valid-only and the cost per model, as tables in SI Section S9⟧

⟦PENDING: rating study — the four results named in Section 5.5, with intervals: the share of the grader's task successes that people call the same, the share of the other answers that people call different, the same two shares for the target score, and the agreement between raters⟧

### 6.6 Preliminary evidence from the first version of the benchmark (2026)

<div class="box">

**Everything in this box is preliminary.** Findings 1 to 4 come from a pilot run of
{{run.date:date}}: {{oct.spec.n_models}} models, the scene track only, {{mvs.n_tasks}} tasks on
{{mvs.n_structures}} structures, {{mvs.spec.samples_per_task:word}} answer per task. Finding 5 comes
from the July 2026 run of the call-list tasks of the first version, under the grader of that
time, and Finding 6 from a small trial of the rating study on the answers of the pilot run.
None of the pilot run's tasks is in the corpus of Section 3. Its answers were archived and
are graded here with the present grader (Section 4) against the references of that time, so
the scores differ somewhat from those published in October with the earlier grader. With one answer per task and
{{mvs.n_structures}} structures, the numbers below can show patterns; they cannot rank the
leading models.

**Finding 1: whether the answer was valid decided the ranking.** Of {{oct.spec.n:,}} answers,
{{oct.spec.n_valid}} ({{oct.spec.valid_share:.0%}}) were valid scenes. Per model the share
ranged from {{oct.spec.valid_share_min:.0%}} to {{oct.spec.valid_share_max:.0%}}, and strict F1
from {{oct.spec.f1_min:.2f}} to {{oct.spec.f1_max:.2f}} (Table 13, columns *Valid answers*
and *F1, strict*). The two are nearly proportional: the Pearson correlation between a
model's share of valid answers and its strict F1 is r = {{oct.spec.r_valid_f1:.2f}}
({{oct.spec.n_models}} models). With the strict task success rate, by which Table 13 is
ordered, the correlation is r = {{oct.spec.r_valid_success:.2f}}. Valid-only, the models are much
closer (F1 from {{oct.spec.valid.f1_min:.2f}} to {{oct.spec.valid.f1_max:.2f}}). Of the
{{mvs.spec.n_failed}} invalid answers, {{mvs.spec.outcome.invalid_json}} were not parseable
JSON. The text of {{mvs.spec.json_shape.n_raw}} of these was archived. In
{{mvs.spec.json_shape.brace_count_share:.0%}} of the {{mvs.spec.json_shape.n_raw}}, the
numbers of opening and closing braces differed: a scene is a deeply nested tree, and one
brace too many or too few loses the whole answer. An offline repair of the JSON turned
{{mvs.spec.repair.n_scene}} of the {{mvs.spec.repair.n_raw}} into scene trees (these were
not checked by the viewer). This is why the final run reports strict and valid-only scores
together and adds a JSON-mode condition.

**Table 13. Pilot run, per model (preliminary).** The run had {{mvs.n_tasks}} tasks and one
answer per task; the rows are ordered by the strict task success rate. Finding 1 compares the
columns *Valid answers* and *F1, strict*. *Weights*: open if the weights of the model can be downloaded,
closed if the model can be used only through a provider's service. *Valid answers*: answers
that parse and that the viewer accepts. *F1*: how much of the drawn state is right (0 to 1).
*Task success rate*: share of answers whose drawn state is exactly right. *Strict*: every answer
counts, and an unshowable answer scores 0. *Valid-only*: the mean over valid answers. The
pilot tasks stored no target, so there is no target score.

{{include:generated/table_october_models.md}}

**Finding 2: clinical tasks lost their points on unrequested context, not on the residue.**
The clinical category scored lowest: strict F1 {{oct.spec.clinical.f1:.2f}}, and task success
{{oct.spec.clinical.success:.1%}}, that is {{oct.spec.clinical.success_n}} of
{{oct.spec.clinical.n}} answers (Table 14, Figure 6). The natural reading is that finding the
residue of a variant is hard. That reading is wrong for this run. In
{{oct.spec.clinical.highlight_exact_n}} answers the requested residue was drawn exactly as in
the reference: same atoms, same representation, same colour. That is
{{oct.spec.clinical.highlight_exact:.0%}} of all {{oct.spec.clinical.n}} answers and
{{oct.spec.clinical.highlight_valid_share:.0%}} of the {{oct.spec.clinical.n_valid}} valid
ones. The points were lost elsewhere. Each clinical reference of the first version also drew
a grey cartoon of the whole protein, and the requests asked only for the residue. An answer
that drew the residue alone was missing a fact; an answer that drew the cartoon differently had
a wrong one. There was a second flaw: all {{mvs.spec.regime.Clinical.n_tasks}} clinical tasks
used a single structure, in which author numbers equal UniProt numbers. The residue could be
found without any mapping, so the category could not test the mapping at all. "Most answers
drew the right residue" is therefore a statement about drawing, not about mapping. Table 15
(rows 1 and 2) says what replaced both.

**Table 14. Pilot run by category, all models pooled (preliminary).** *Answers*: one per model
and task. *Valid*: answers that parse and that the viewer accepts. *F1, earlier grader*: the
score under the grader used in October, for comparison. *F1* and *task success rate*: as in
Table 13, strict, over all answers of the row. *Requested part exactly right*: this column has its
own denominator, given in each cell. Among answers to tasks whose reference marks out a
requested part against a background, it is the share that draw that part with exactly the
reference's atoms, representation and colour (an unshowable answer counts as wrong). It is the
forerunner of the target score of Section 4.2: the pilot tasks stored no target atoms, so the
requested part is taken from the reference. The first-version corpus had too few tasks in
three of its categories to show them apart, so they are pooled in one row. The last cell of
the row *All* pools the three cells above it.

{{include:generated/table_october_regrade.md}}

![**Figure 6. Pilot run: three scores by category (preliminary).** All three are on a scale from 0 to 1 and are printed in that form (0.70 is 70% of answers; Table 14 gives the shares as percentages). *F1* (how much of the drawn state is right; a mean score) and *task success* (the share of answers whose drawn state is exactly right) are taken strictly, over all answers of all {{oct.spec.n_models}} models; an unshowable answer scores 0. *Requested part exactly right* has a smaller denominator in two of the three groups: it is the share, among answers to tasks whose reference marks out a requested part against a background, that draw that part exactly as the reference does, whatever the rest of the answer shows; an unshowable answer counts as wrong. The number of answers behind each bar is printed above it (n); for the third bar of a group this is the number of answers to tasks that mark a requested part. Three categories with few tasks are pooled in the middle group. In the clinical category, where every task marks a requested part, that part was usually right and the whole drawn state almost never.](generated/fig_october_regrade.svg)

**Finding 3: grounding packs did not help.** In the pilot run, unlike the final design, every
task had a grounding pack. Appending it to the request lowered task success over all
{{mvs.n_tasks}} tasks from {{oct.spec.success:.1%}} to
{{oct.spec_grounded.success:.1%}}, and the number of valid answers from {{oct.spec.n_valid}} to
{{oct.spec_grounded.n_valid}}: the longer prompt produced more invalid answers. In the clinical
category, task success was {{oct.spec.clinical.success:.1%}} without the pack and
{{oct.spec_grounded.clinical.success:.1%}} with it. Finding 2 explains why the pack had little
to add: the residue was already right without it. Whether a pack helps when it holds a number
that the model cannot guess is a question for the rebuilt clinical category (Table 10).

**Finding 4: without the format guide, no answer was valid.** The condition with the
instruction and the rule for the answer only was run on {{mvs.bare.n_models}} models, with and
without grounding packs. None of their {{mvs.bare.n_samples}} answers was a valid scene. For
these models, knowledge of the MolViewSpec format came from the prompt and not from training.

**Finding 5: the call-list track of the first version did not separate models from a keyword
script.** That track had {{legacy_api.n_tasks}} hand-written tasks and a grader that compared
call lists field by field. Under that grader the keyword script reached a mean F1 of
{{legacy_api.baseline_f1:.2f}}, and the {{legacy_api.n_models}} models scored between
{{legacy_api.f1_min:.2f}} and {{legacy_api.f1_max:.2f}} (run of {{legacy_api.run:date}}). These
numbers are the reason the track was rebuilt; they are not results of the present benchmark.

**Finding 6: the trial of the rating study was too small to validate anything.** In October,
{{pilot.n_raters:word}} raters, one of them an author, gave {{pilot.all.n_labelled}} verdicts
of "same" or "different" on {{pilot.all.n_pairs}} picture comparisons of valid scenes that
the earlier grader scored below 1. Only {{pilot.all.pairs_two_raters}} comparisons received
two verdicts, so agreement between people cannot be estimated. The trial validates neither
the image judge (Section 5.5) nor the grader, and no score in this paper uses the image
judge. SI Section S8.1 reports the trial in full, with the agreement between people and the
image judge and with its limits.

*End of the preliminary evidence.*

</div>
