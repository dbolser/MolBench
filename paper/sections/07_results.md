## 6. Results

Sections 6.1 to 6.5 show every result table in its final shape. The cells wait for the one
paid run and are filled by script from its archive; the layout, the captions and the
definitions will not change. In this draft the two tables with one row per model show their
first rows only. Section 6.6 is different: it reports, in a box, what a pilot run in October
2026 showed. Those numbers are real but come from an older corpus, and they are kept apart
from everything else.

![**Figure 5. The result figures that the final run will fill.** No data are shown. **A**: task success rate per model on both tracks, with 95% intervals; *task success rate* is the share of answers whose drawn state is exactly right, and an answer that cannot be shown counts as wrong (strict). **B**: for each model, its pairs split by which side was right; a side is *right* when at least two of its three answers have a target score of 1. **C**: task success rate and target score per tier, valid-only (the mean over valid answers), so that the gap between the two marks shows unrequested drawing and not unparseable answers; *target score* asks only whether the requested atoms are drawn as asked.](generated/fig_result_shapes.svg)

### 6.1 Models on both tracks

**Table 5. Scene track, main condition (format reference).** One row per model; † marks an
optional model. *Valid answers*: share of answers that parse and that the viewer accepts. *F1*:
how much of the drawn state is right (0 to 1). *Task success*: share of answers whose drawn
state is exactly right (the task success rate). *Target score*: whether the requested atoms
are drawn as asked, whatever else was drawn (0 to 1). *Strict*: every answer counts, and an
answer that cannot be shown scores 0. *Valid-only*: the mean over valid answers. *All 3
samples right*: share of tasks on which every one of the three answers is exactly right. *Cost*: US dollars for all calls of the model in this
condition, at list price. Intervals (95%, structures resampled) will be given with each score.

{{include:generated/table_final_leaderboard_scene.md|else:generated/shape_leaderboard.md}}

**Table 6. Call-list track, main condition.** Same columns and definitions as Table 5, except
that a *valid answer* is a JSON list that fits the call schema, and a call list that breaks
the schema keeps, under *strict*, the scores it earns when replayed (Section 4.4).

{{include:generated/table_final_leaderboard_calls.md|PENDING: final run — the table for the call-list track, in the shape of Table 5}}

### 6.2 Tiers

**Table 7. Scores by tier and track**, mean over the models of the panel (the keyword script
is left out). *F1*, *task success* and *target score* as in Table 5. *Strict*: every answer
counts, and an answer that cannot be shown scores 0. *Valid-only*: the mean over valid
answers, which shows the difficulty of a tier once the format has been written correctly.

{{include:generated/table_final_tiers.md|else:generated/shape_tiers.md}}

### 6.3 The same request in two formats

**Table 8. Paired comparison of the two formats.** For each model, its
{{corpus.n_twin_pairs}} pairs (one request on both tracks, same target atoms) are split four
ways, twice. A side is *right* when at least two of its three answers are right. *Target-right*
columns (primary): an answer is right when its target score is 1, that is, the requested
atoms are drawn exactly as asked; this is the same test in both formats. *Task success*
columns (secondary): an answer is right when its whole drawn state is exactly right; this is
not the same test in the two formats (Section 3.4). *Both*, *scene only*, *call list only*,
*neither*: the number of pairs right on both sides, on one side only, or on neither. *McNemar
p*: exact test that the two one-sided counts are equal; a small value means that one format
is harder for this model. † marks an optional model.

{{include:generated/table_final_paired.md|else:generated/shape_paired.md}}

Where both formats demand the same knowledge, which is every tier with pairs except the
clinical one, a pair that is target-right on one side only points to the format: the model
knew which atoms were meant and failed to write them in the other format. A pair that is
wrong on both sides is a candidate for an error of content. Clinical pairs must be read
differently. There a right call list does not show that the model knew the residue, because
the viewer can do the mapping (Section 3.4); "call list right, scene wrong" then points to the
mapping, not to the scene format. The counts without the clinical pairs are the cleaner test
of the formats.
⟦PENDING: final run — the same counts without the clinical pairs, and without the {{corpus.twins.need_hide_toggle}} pairs in which the call list must switch off part of the default drawing⟧

### 6.4 Clinical variants

**Table 9. Clinical tier on the scene track, by what the request demands.** *Task success* and
*target score* as in Table 5, strict, mean over the models of the panel. *Grounding pack*: the
result of the lookup, including the mapped residue, appended to the request (Table 4). The
rows are two different splits of the same {{clin.n}} tasks (Section 3.3). *Split A*: would an
answer that copies the number in the variant name as the author residue number be right?
*Split B*: is the target residue numbered as in UniProt? The splits differ in the tasks that
use a traditional name counted along the mature protein. The helix and strand tasks need the
entry's own annotation; they are a subset of the {{clin.n}} and are also reported apart.

{{include:generated/table_final_clinical.md|else:generated/shape_clinical.md}}

This table carries the benchmark's central question. If models read variant numbers at face
value, task success will be high in the first row of Split A and low in the second, and the
grounding pack will close the gap. If models carry out the mapping, the two rows will be
alike.

### 6.5 Follow-up turns, open requests and robustness

**Table 10. Follow-up turns and requests with several right answers.** *Task success*: share
of answers whose drawn state is exactly right (for a request with several right answers: the
drawn state equals any one of the accepted answers), strict, mean over the models of the
panel.

{{include:generated/table_final_followup.md|else:generated/shape_followup.md}}

**Table 11. Planned comparisons.** Each row compares the task success rate (strict, mean over
the models of the panel) between two groups of tasks or two conditions, with a 95% interval on
the difference (structures resampled). *JSON mode*: the provider's option that forces
syntactically valid JSON; that condition has 1 sample per task. *Grounding pack*: as in Table
9. *Format reference*: the reference text for the answer format in the system prompt.

{{include:generated/table_final_robustness.md|else:generated/shape_robustness.md}}

⟦PENDING: final run — outcome counts per model (valid, invalid JSON, rejected by the viewer, cut off), the repaired scores and the cost per model, as tables in SI Section S8⟧

⟦PENDING: rating study — agreement between people, and between people and the grader's task success, with intervals (Section 5.5)⟧

### 6.6 Preliminary evidence (October 2026 pilot run: older corpus, regraded with the present grader)

<div class="box">

**Everything in this box is preliminary.** It comes from a pilot run of {{run.date}}:
{{oct.spec.n_models}} models, the scene track only, {{mvs.n_tasks}} tasks on
{{mvs.n_structures}} structures, {{mvs.spec.samples_per_task}} answer per task. The tasks were
an earlier corpus; none of them is in the corpus of Section 3. The answers were archived and
are graded here with the present grader (Section 4) against the references of that time, so the
scores differ somewhat from those published in October with the earlier grader. With one
sample and {{mvs.n_structures}} structures, the numbers below can show patterns; they cannot
rank the leading models.

**Finding 1: whether the answer was valid decided the ranking.** Of {{oct.spec.n:,}} answers,
{{oct.spec.n_valid}} ({{oct.spec.valid_share:.0%}}) were valid scenes. Per model the share
ranged from {{oct.spec.valid_share_min:.0%}} to {{oct.spec.valid_share_max:.0%}}, and strict F1
from {{oct.spec.f1_min:.2f}} to {{oct.spec.f1_max:.2f}} (Table P1). The two are nearly the same
ranking: the correlation between a model's share of valid answers and its strict F1 is
r = {{oct.spec.r_valid_f1:.2f}}. Valid-only, the models are much closer (F1 from
{{oct.spec.valid.f1_min:.2f}} to {{oct.spec.valid.f1_max:.2f}}). Of the
{{mvs.spec.n_failed}} invalid answers, {{mvs.spec.outcome.invalid_json}} were not parseable
JSON, and {{mvs.spec.json_shape.brace_count_share:.0%}} of the {{mvs.spec.json_shape.n_raw}}
whose text was archived opened and closed a different number of braces. A scene is a deeply
nested tree, and one brace too many or too few loses the whole answer. An offline repair of
the JSON turned {{mvs.spec.repair.n_scene}} of those {{mvs.spec.repair.n_raw}} answers into
scene trees (these were not checked by the viewer). This is why the final run reports strict
and valid-only scores side by side and adds a JSON-mode condition.

**Table P1. Pilot run, per model (preliminary).** {{mvs.n_tasks}} tasks, one answer each,
ordered by task success. *Valid answers*: answers that parse and that the viewer accepts.
*F1*: how much of the drawn state is right (0 to 1). *Task success*: share of answers whose
drawn state is exactly right. *Strict*: every answer counts, and an answer that cannot be
shown scores 0. *Valid-only*: the mean over valid answers.

{{include:generated/table_october_models.md}}

**Finding 2: clinical tasks lost their points on unrequested context, not on the residue.**
The clinical tier scored lowest: strict F1 {{oct.spec.clinical.f1:.2f}}, and task success
{{oct.spec.clinical.success:.1%}}, that is {{oct.spec.clinical.success_n}} of
{{oct.spec.clinical.n}} answers (Table P2, Figure 6). The natural reading is that finding the
residue of a variant is hard. That reading is wrong for this run. In
{{oct.spec.clinical.highlight_exact_n}} of the {{oct.spec.clinical.n}} answers, which is
{{oct.spec.clinical.highlight_valid_share:.0%}} of the {{oct.spec.clinical.n_valid}} valid ones,
the requested residue was drawn exactly as in the reference: same atoms, same representation,
same colour. The points were lost elsewhere. Each clinical reference of that corpus also drew
a grey cartoon of the whole protein, and the requests asked only for the residue. An answer
that drew the residue alone was missing a fact; an answer that drew the cartoon differently had
a wrong one. There was a second flaw: all {{mvs.spec.regime.Clinical.n_tasks}} clinical tasks
used {{mvs.spec.regime.Clinical.n_structures}} structure, in which author numbers equal UniProt
numbers. The residue could be found without any mapping, so the tier could not test the
mapping at all.

**Table P2. Pilot run by tier, all models pooled (preliminary).** *Answers*: one per model and
task. *Valid*: answers that parse and that the viewer accepts. *F1, earlier grader*: the score
under the grader used in October, for comparison. *F1* and *task success*: as in Table P1,
strict. *Requested part exactly right*: among answers to tasks whose reference marks out a
requested part against a background, the share that draw that part with exactly the
reference's atoms, representation and colour (strict). It is the forerunner of the target
score of Section 4.2: the pilot tasks stored no target atoms, so the requested part is taken
from the reference. The October corpus had too few tasks in three of its tiers to show them
apart, so they are pooled in one row.

{{include:generated/table_october_regrade.md}}

![**Figure 6. Pilot run: three scores by tier (preliminary).** Strict means over all answers of all {{oct.spec.n_models}} models. *F1*: how much of the drawn state is right. *Task success*: drawn state exactly right. *Requested part exactly right*: the residues or ligand the request is about drawn exactly as in the reference, whatever the rest of the answer shows; it is the forerunner of the target score. Three tiers with few tasks are pooled in the middle group. In the clinical tier the requested part was usually right and the whole drawn state almost never.](generated/fig_october_regrade.svg)

**How Finding 2 changed the design.** (i) A reference now holds only what the request
states; if context is wanted, the request asks for it in words. (ii) Every task stores its
target atoms, and the target score is reported next to F1 and task success, so that context
and substance can no longer be confused. (iii) An attribute that the request does not state is
free (Section 3.5). (iv) The clinical tier was rebuilt: {{clin.n}} tasks on
{{clin.n_proteins}} proteins, {{clin.n_offset}} of them with a numbering offset, in place of
{{mvs.spec.regime.Clinical.n_tasks}} tasks on one protein with none.

**Finding 3: grounding packs did not help.** Appending each task's grounding pack to the
request lowered task success over all tasks from {{oct.spec.success:.1%}} to
{{oct.spec_grounded.success:.1%}}, and the number of valid answers from {{oct.spec.n_valid}} to
{{oct.spec_grounded.n_valid}}: the longer prompt produced more invalid answers. On the clinical
tier, task success was {{oct.spec.clinical.success:.1%}} without the pack and
{{oct.spec_grounded.clinical.success:.1%}} with it. Finding 2 explains why the pack had little
to add: the residue was already right without it. Whether a pack helps when it holds a number
that the model cannot guess is a question for the rebuilt clinical tier (Table 9).

**Finding 4: without the format reference, no answer was valid.**
The condition with the instruction and the rule for the answer only was run on {{mvs.bare.n_models}}
models, with and without grounding packs. None of their {{mvs.bare.n_samples}} answers was a
valid scene. For these models, knowledge of the
MolViewSpec format came from the prompt and not from training.

**Finding 5: our first call-list track did not separate models from a keyword script.** That
track had {{legacy_api.n_tasks}} hand-written tasks and a grader that compared call lists field
by field. Under that grader the keyword script reached a mean F1 of
{{legacy_api.baseline_f1:.2f}}, and the {{legacy_api.n_models}} models between
{{legacy_api.f1_min:.2f}} and {{legacy_api.f1_max:.2f}} (run of {{legacy_api.run}}). These numbers are the reason the track
was rebuilt; they are not results of the present benchmark.

**Finding 6: the pilot rating study was too small to validate anything.** *What was done.* In
October, each valid scene that scored below 1 was rendered, and an image judge (Section 5.5)
was shown its picture beside the picture of the reference. Volunteers then judged a sample of
the same picture comparisons. {{pilot.n_raters}} raters, one of them an author, gave
{{pilot.all.n_labelled}} verdicts of "same" or "different" on {{pilot.all.n_pairs}} picture
comparisons.

*Result.* People and the image judge gave the same verdict in {{pilot.all.agreement:.0%}} of
cases. Cohen's kappa, which is agreement beyond what chance would give (0 is chance, 1 is
perfect), was {{pilot.all.kappa:.2f}} (95% interval {{pilot.all.kappa_lo:.2f}} to
{{pilot.all.kappa_hi:.2f}}). Where the judge had said "same", people agreed in
{{pilot.all.rescue:.0%}} of cases ({{pilot.all.rescue_lo:.0%}} to
{{pilot.all.rescue_hi:.0%}}), or in {{pilot.indep.rescue:.0%}} ({{pilot.indep.rescue_lo:.0%}}
to {{pilot.indep.rescue_hi:.0%}}) when the author's verdicts are left out.

*Limits.* Only {{pilot.n_raters_passing_checks}} of the {{pilot.n_raters}} raters met the
attention-check rule that was written before the data were seen (at least
{{pilot.check_rule:.0%}} right on each kind of check item): the author was never shown a check
item, and one volunteer answered "can't tell" on a check, which the rule counts as a miss. The
numbers above include all raters and so depart from that rule. Only
{{pilot.all.pairs_two_raters}} picture comparisons received two verdicts, so agreement between
people cannot be estimated. The pilot does not validate the image judge, and it supports no
statement about tiers, single models or the final run. No score in this paper uses the image
judge: under the earlier grader, counting the judge's "same" verdicts as right changed no
model's mean F1 by more than {{mvs.spec.escalation.lift_max:.3f}}.

*End of the preliminary evidence.*

</div>
