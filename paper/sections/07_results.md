## 6. Results

The only results that exist today come from a pilot run in October 2026 on an older corpus.
They are real, they are kept apart from everything else, and they are in the box of Section
6.6. Sections 6.1 to 6.5 show the tables that the one paid run will fill: their layout,
captions and definitions are fixed, and the cells are filled by script from the archive of the
run. Figure 5 shows the layout of the three result figures. In this draft the tables with one
row per model (Tables 6, 9a and 9b) show their first rows only, and Table 7 is described but
not drawn.

![**Figure 5. The result figures that the final run will fill (no data shown).** **A**: task success rate (the share of answers whose drawn state is exactly right) per model, strict, with 95% intervals, one panel per track. The two panels must not be compared with each other (Section 4.2); formats are compared in panel B only. **B**: for each model, its {{corpus.twins.n_with_target}} pairs that have a target score, by which side was right (at least 2 of its {{plan.samples}} answers target-right, that is, with a target score of exactly 1). **C**: task success rate and target score (the requested atoms drawn as asked, whatever else was drawn) per category, over valid answers only; a target score well above the task success rate means that the requested atoms were right and something else was not.](generated/fig_result_shapes.svg)

### 6.1 Models on both tracks

**Table 6. Scene track, main condition.** One row per model; † marks an optional model.
*Weights*: open if the weights of the model can be downloaded, closed if the model can be
used only through a provider's service. *Valid answers*: share of answers that parse and that
the viewer accepts. *Task success rate*: share of answers whose drawn state is exactly right.
*Target score*: whether the requested atoms are drawn as asked, whatever else was drawn (0 to
1). *F1*: how much of the drawn state is right (0 to 1). *Strict*: every answer counts, and an
unshowable answer scores 0. *Valid-only*: the mean over valid answers. *All-{{plan.samples}} rate*: share of
tasks on which all {{plan.samples}} answers are exactly right. *Cost*: US dollars for all calls of the
model in this condition, at list price. Intervals (95%, structures resampled) will be given
with each score. F1 valid-only is in the SI.

{{include:generated/table_final_leaderboard_scene.md|else:generated/shape_leaderboard.md}}

**Table 7. Call-list track, main condition.** Same columns and definitions as Table 6, except
that a *valid answer* is a JSON list that fits the call schema, and a schema-breaking call list
keeps, under *strict*, the scores it earns when replayed (Section 4.4).

{{include:generated/table_final_leaderboard_calls.md|PENDING: final run — the table for the call-list track, in the shape of Table 6}}

### 6.2 Categories

**Table 8. Scores by category and track**, mean over the models (the keyword script is left
out). *Structures*: the number of structures that the tasks of the row sit on, which is the
number of units resampled for its intervals. *Task success rate*, *target score* and *F1* as
in Table 6. *Strict*: every answer counts, and an unshowable answer scores 0. *Valid-only*:
the mean over valid answers, which shows the difficulty of a category once the format has been
written correctly. The two rows marked *of which* divide the answers of the name-resolution
category by the entry that the model chose: the entry of the reference, or another accepted
entry (Section 3.3); they are sets of answers, so they have no number of tasks.

{{include:generated/table_final_tiers.md|else:generated/shape_tiers.md}}

### 6.3 The same request in two formats

**Table 9. Paired comparison of the two formats.** For each model, its pairs (one request on
both tracks, same target atoms) are divided into four cells, in two tables. A side of a pair
is *right* when at least 2 of its {{plan.samples}} answers are right. *Table 9a* (primary): an
answer is right when it is target-right, that is, its target score is 1 and the requested
atoms are drawn exactly as asked; this is the same test in both formats. Table 9a covers the
{{corpus.twins.n_with_target}} pairs that have a target score; the other
{{corpus.twins.n_without_target}}, all follow-up pairs, have none (Sections 4.2 and 5.4) and
appear in Table 9b only. *Table 9b* (secondary): an answer is right
when it is a task success, that is, its whole drawn state is exactly right; this is not the
same test in the two formats (Section 4.2). Table 9b covers all {{corpus.n_twin_pairs}}
pairs. An unshowable answer is not right. The four count columns give the number of pairs right
on both sides, on one side only, or on neither. *McNemar p*: exact test that the two one-sided
counts are equal; a small value means that one format is harder for this model. † marks an
optional model.

{{include:generated/table_final_paired.md|else:generated/shape_paired.md}}

Where both formats demand the same knowledge, which is every category with pairs except the
clinical one, a pair that is target-right on one side only points to the format: the model
produced the right atoms in one format and not in the other, either because the other answer
could not be shown or because it selected other atoms. A pair that is wrong on both sides is a
candidate for an error of content. Clinical pairs must be read differently. There a right call
list does not show that the model knew the residue, because the viewer can do the mapping
(Section 3.4); "call list right, scene wrong" then points to the mapping, not to the scene
format. The counts without the clinical pairs are the cleaner test of the formats.
⟦PENDING: final run — the same counts without the clinical pairs, and without the {{corpus.twins.need_hide_toggle}} pairs in which the call list must switch off part of the default view; and, in the SI, the one-sided pairs divided by whether the side that was not right was unshowable⟧

### 6.4 Clinical variants

**Table 10. Clinical category on the scene track, where the model must map the number itself, by whether copying the number from the variant name is right.** *Target score*
(the requested residue drawn as asked, whatever else was drawn) and *task success rate* (drawn
state exactly right), strict, mean over the models. *With grounding pack*: the result of the
lookup, including the mapped residue, is appended to the request. The rows are two
groupings of the same {{clin.n}} tasks (Section 3.3.1, Table 2). *Copying the number*: an
answer that uses the number printed in the variant name as the author residue number is right,
or wrong. *Offset*: the author number of the target residue differs from its UniProt number,
or does not. The *difference* row is the planned comparison of Section 5.4. *Matched tasks*:
the same variant asked on a structure with an offset and on a predicted structure without one
({{clin.n_offset_pairs}} sets; descriptive only). In the helix and strand tasks the model
must also know where the entry records that helix or strand to begin and end; they are a
subset of the {{clin.n}} and are also reported apart.

{{include:generated/table_final_clinical.md|else:generated/shape_clinical.md}}

This table answers the question of the Introduction: do models map the number in a variant
name, or copy it? Four patterns are possible.

1. *Copying.* The target score is high where copying is right and low where it is wrong, and
   the grounding pack closes the gap.
2. *Mapping.* The two rows are alike, and both are high.
3. *Always converting.* A model that changes the number whatever the entry is wrong where
   copying is right, and the gap is reversed. Scoring well in both rows therefore needs more
   than a habit of copying or of converting: the model must know how each entry is numbered.
4. *Neither.* If the target score is low in both rows, the loss lies elsewhere, for example
   in the chain identifier or in invalid answers, and the table does not decide between
   copying and mapping.

The prediction is stated on the target score, because the task success rate also falls when
an answer adds unrequested context.

### 6.5 Follow-up turns, requests with several right answers, and planned comparisons

Table 11 divides the follow-up turns by whether a change is needed, and Table 12 holds the
planned comparisons 1 to 6 of Section 5.4.

**Table 11. Follow-up turns and requests with several right answers.** *Task success rate*:
share of answers whose drawn state is exactly right (for a request with several right answers:
the drawn state equals any one of the accepted answers), strict, mean over the models.

{{include:generated/table_final_followup.md|else:generated/shape_followup.md}}

**Table 12. Planned comparisons 1 to 6 of Section 5.4.** Each row compares the task success rate (share of answers
whose drawn state is exactly right; strict, mean over the models) between two groups of tasks
or two conditions, with a 95% interval on the difference (structures resampled). *Main*: the
main condition. *JSON mode*: the provider's option that forces syntactically valid JSON; that
condition has one answer per task. *Grounding pack*: the result of an offline lookup,
including the mapped residue or the list of entries, appended to the request. *Format guide*: the text in
the system prompt that documents the answer format.

{{include:generated/table_final_robustness.md|else:generated/shape_robustness.md}}

⟦PENDING: final run — outcome counts per model (valid, unshowable by kind, schema-breaking, cut off), the repaired scores, F1 valid-only and the cost per model, as tables in SI Section S9⟧

⟦PENDING: rating study — the share of answers not counted as a success that people judge to show the same as the reference, the agreement between raters, the agreement between people and the image judge, and the check of possible false passes, with intervals (Section 5.5)⟧

### 6.6 Preliminary evidence (October 2026 pilot run: older corpus, regraded with the present grader)

<div class="box">

**Everything in this box is preliminary.** Findings 1 to 4 come from a pilot run of
{{run.date:date}}: {{oct.spec.n_models}} models, the scene track only, {{mvs.n_tasks}} tasks on
{{mvs.n_structures}} structures, {{mvs.spec.samples_per_task:word}} answer per task. Finding 5 comes
from an earlier run of our first call-list track, and Finding 6 from a small trial of the
rating study on the October answers. The tasks of the pilot run were an earlier corpus; none of
them is in the corpus of Section 3. The answers were archived and are graded here with the
present grader (Section 4) against the references of that time, so the scores differ somewhat
from those published in October with the earlier grader. With one answer per task and
{{mvs.n_structures}} structures, the numbers below can show patterns; they cannot rank the
leading models.

**Finding 1: whether the answer was valid decided the ranking.** Of {{oct.spec.n:,}} answers,
{{oct.spec.n_valid}} ({{oct.spec.valid_share:.0%}}) were valid scenes. Per model the share
ranged from {{oct.spec.valid_share_min:.0%}} to {{oct.spec.valid_share_max:.0%}}, and strict F1
from {{oct.spec.f1_min:.2f}} to {{oct.spec.f1_max:.2f}} (Table 13, columns *Valid answers*
and *F1 (strict)*). The two are nearly the same ranking: the Pearson correlation between a
model's share of valid answers and its strict F1 is r = {{oct.spec.r_valid_f1:.2f}}
({{oct.spec.n_models}} models). With the strict task success rate, by which Table 13 is
ordered, the correlation is r = {{oct.spec.r_valid_success:.2f}}. Valid-only, the models are much
closer (F1 from {{oct.spec.valid.f1_min:.2f}} to {{oct.spec.valid.f1_max:.2f}}). Of the
{{mvs.spec.n_failed}} invalid answers, {{mvs.spec.outcome.invalid_json}} were not parseable
JSON. The text of {{mvs.spec.json_shape.n_raw}} of these was archived (the pilot archive holds
no text for the rest), and {{mvs.spec.json_shape.brace_count_share:.0%}} of them opened and
closed a different number of braces. A scene is a deeply nested tree, and one brace too many
or too few loses the whole answer. An offline repair of the JSON turned
{{mvs.spec.repair.n_scene}} of those {{mvs.spec.repair.n_raw}} answers into scene trees (these
were not checked by the viewer). This is why the final run reports strict and valid-only scores
side by side and adds a JSON-mode condition.

**Table 13. Pilot run, per model (preliminary).** The run had {{mvs.n_tasks}} tasks and one
answer per task; the rows are ordered by the strict task success rate. Finding 1 compares the
columns *Valid answers* and *F1 (strict)*. *Weights*: open if the weights of the model can be downloaded,
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
ones. The points were lost elsewhere. Each clinical reference of that corpus also drew
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
requested part is taken from the reference. The October corpus had too few tasks in three of
its categories to show them apart, so they are pooled in one row.

{{include:generated/table_october_regrade.md}}

![**Figure 6. Pilot run: three scores by category (preliminary).** *F1* (how much of the drawn state is right; a mean score from 0 to 1) and *task success* (the share of answers whose drawn state is exactly right, printed as a percentage) are taken strictly, over all answers of all {{oct.spec.n_models}} models; an unshowable answer scores 0. *Requested part exactly right* has a smaller denominator in two of the three groups: it is the share, among answers to tasks whose reference marks out a requested part against a background, that draw that part exactly as the reference does, whatever the rest of the answer shows; an unshowable answer counts as wrong. The number of answers behind each bar is printed above it (n); for the third bar of a group this is the number of answers to tasks that mark a requested part. Three categories with few tasks are pooled in the middle group. In the clinical category, where every task marks a requested part, that part was usually right and the whole drawn state almost never.](generated/fig_october_regrade.svg)

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

**Finding 5: our first call-list track did not separate models from a keyword script.** That
track had {{legacy_api.n_tasks}} hand-written tasks and a grader that compared call lists field
by field. Under that grader the keyword script reached a mean F1 of
{{legacy_api.baseline_f1:.2f}}, and the {{legacy_api.n_models}} models scored between
{{legacy_api.f1_min:.2f}} and {{legacy_api.f1_max:.2f}} (run of {{legacy_api.run:date}}). These
numbers are the reason the track was rebuilt; they are not results of the present benchmark.

**Finding 6: the trial of the rating study was too small to validate anything.** In October,
each valid scene that the earlier grader scored below 1 was rendered, and an image judge
(Section 5.5) was shown its picture beside the picture of the reference. Volunteers then
judged a sample of the same picture comparisons, to see whether such answers looked the same
as the reference to people. In all, {{pilot.n_raters}} raters, one of them an author, gave
{{pilot.all.n_labelled}} verdicts of "same" or "different" on {{pilot.all.n_pairs}} picture
comparisons. People and the image judge gave the same verdict in
{{pilot.all.agreement:.0%}} of cases (Cohen's kappa, which is agreement beyond chance,
{{pilot.all.kappa:.2f}}; 95% interval {{pilot.all.kappa_lo:.2f}} to
{{pilot.all.kappa_hi:.2f}}). Only {{pilot.all.pairs_two_raters}} picture comparisons received
two verdicts, so agreement between people cannot be estimated. The trial does not validate
the image judge or the grader, and it supports no statement about categories, single models
or the final run. No score in this paper uses the image judge. SI Section S8.1 reports the
trial in full, with its limits.

*End of the preliminary evidence.*

</div>
