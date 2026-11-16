## 6. Results

Sections 6.1 to 6.5 show every result table in its final shape. The cells wait for the one
paid run and are filled by script from its archive; the layout, the captions and the
definitions will not change. Section 6.6 is different: it reports, in a box, what a pilot run
in October 2026 showed. Those numbers are real but come from an older corpus, and they are
kept apart from everything else.

![**Figure 5. The result figures that the final run will fill.** No data are shown. **A**: task success per model on both tracks, with 95% intervals; *task success* is the share of answers whose drawn state is exactly right, with an invalid answer counted as wrong (strict). **B**: for each model, its pairs split by which side was right. **C**: task success and target score per tier over valid outputs; *target score* asks only whether the requested atoms are drawn as asked, so a gap between the two marks is unrequested extra drawing.](generated/fig_result_shapes.svg)

### 6.1 Models on both tracks

**Table 5. Scene track, headline condition (format reference).** One row per model; † marks an
optional model. *Valid outputs*: share of answers that parse and that the viewer accepts. *F1*:
how much of the drawn state is right (0 to 1). *Task success*: share of answers whose drawn
state is exactly right. *Target score*: whether the requested atoms are drawn as asked,
whatever else was drawn (0 to 1). *Strict*: an invalid answer counts as 0. *Valid outputs
only*: the mean over valid answers. *All 3 samples right*: share of tasks on which every
sampled answer is exactly right. *Cost*: US dollars for all calls of the model in this
condition, at list price. Intervals (95%, structures resampled) will be given with each score.

{{include:generated/table_final_leaderboard_scene.md|else:generated/shape_leaderboard.md}}

**Table 6. Call-list track, headline condition.** Same columns and definitions as Table 5.

{{include:generated/table_final_leaderboard_calls.md|PENDING: final run — the table for the call-list track, in the shape of Table 5}}

### 6.2 Tiers

**Table 7. Scores by tier and track**, mean over models. *F1*, *task success* and *target
score* as in Table 5. *Strict*: an invalid answer counts as 0. *Valid outputs only*: the mean
over valid answers, which shows the difficulty of a tier once the format has been written
correctly.

{{include:generated/table_final_tiers.md|else:generated/shape_tiers.md}}

### 6.3 The same request in two formats

**Table 8. Paired comparison of the two formats.** For each model, its
{{corpus.n_twin_pairs}} pairs (one request on both tracks, same target atoms) are split four
ways. A side is *right* when at least two of its three sampled answers are right, first by
the target score (the requested atoms drawn exactly as asked) and then by task success (the
whole final state exactly right; not the same test in the two formats, Section 3.4). *McNemar p*: exact test that the two one-sided counts are equal; a small value means
that one format is harder for this model. † marks an optional model.

{{include:generated/table_final_paired.md|else:generated/shape_paired.md}}

A model that is right on the scene and wrong on the call list knew which atoms were meant and
failed on the format, and likewise in the other direction. Pairs that are wrong on both sides
are the candidates for an error of content.
⟦PENDING: final run — the same counts without the {{corpus.twins.need_hide_toggle}} pairs that need an unstated hide step, and without the clinical pairs⟧

### 6.4 Clinical variants

**Table 9. Clinical tier on the scene track, by what the request demands.** *Task success* and
*target score* as in Table 5, strict, mean over models. *Grounding pack*: facts about the
structure, including the UniProt mapping, appended to the request. The first two rows split the
tasks by whether an answer that takes the number in the variant name as the author residue
number would be right. Rows overlap; the helix and strand tasks need the entry's own annotation
and are reported apart.

{{include:generated/table_final_clinical.md|else:generated/shape_clinical.md}}

This table carries the benchmark's central question. If models read variant numbers at face
value, task success will be high in the first row and low in the second, and the grounding pack
will close the gap. If models carry out the mapping, the rows will be alike.

### 6.5 Follow-up turns, open requests and robustness

**Table 10. Follow-up turns and requests with several right answers.** *Task success*: share
of answers whose final drawn state is exactly right (for requests with several right answers:
exactly one of the accepted states), strict, mean over models.

{{include:generated/table_final_followup.md|else:generated/shape_followup.md}}

**Table 11. Planned comparisons.** Each row compares task success (strict, mean over models)
between two groups of tasks or two conditions, with a 95% interval on the difference
(structures resampled). *JSON mode*: the provider's option that forces syntactically valid
JSON. *Grounding pack*: as in Table 9. *Format reference*: the reference text for the answer
format in the system prompt.

{{include:generated/table_final_robustness.md|else:generated/shape_robustness.md}}

⟦PENDING: final run — outcome counts per model (valid, invalid JSON, rejected by the viewer, cut off), the JSON-repair counterfactual and the cost per model, as tables in SI Section S8⟧

⟦PENDING: rating study — agreement between people, and between people and the grader's task success, with intervals (Section 5.5)⟧

### 6.6 Preliminary evidence (October 2026 pilot run, older corpus and grader)

<div class="box">

**Everything in this box is preliminary.** It comes from a pilot run of {{run.date}}:
{{oct.spec.n_models}} models, the scene track only, {{mvs.n_tasks}} tasks on
{{mvs.n_structures}} structures, {{mvs.spec.samples_per_task}} sample per task. The tasks were
an earlier corpus; none of them is in the corpus of Section 3. The answers were archived and
are graded here with the present grader (Section 4) against the references of that time, so the
scores differ somewhat from those published in October with the earlier grader. With one
sample and {{mvs.n_structures}} structures, the numbers below can show patterns; they cannot
rank the leading models.

**Finding 1: whether the output was valid decided the ranking.** Of {{oct.spec.n:,}} answers,
{{oct.spec.n_valid}} ({{oct.spec.valid_share:.0%}}) were valid scenes. Per model the share
ranged from {{oct.spec.valid_share_min:.0%}} to {{oct.spec.valid_share_max:.0%}}, and strict F1
from {{oct.spec.f1_min:.2f}} to {{oct.spec.f1_max:.2f}} (Table P1). The two are nearly the same
ranking: the correlation between a model's share of valid outputs and its strict F1 is
r = {{oct.spec.r_valid_f1:.2f}}. Over valid outputs only, the models are much closer (F1 from
{{oct.spec.valid.f1_min:.2f}} to {{oct.spec.valid.f1_max:.2f}}). Of the
{{mvs.spec.n_failed}} invalid answers, {{mvs.spec.outcome.invalid_json}} were not parseable
JSON, and {{mvs.spec.json_shape.brace_count_share:.0%}} of the {{mvs.spec.json_shape.n_raw}}
whose text was archived opened and closed a different number of braces. A scene is a deeply
nested tree, and one brace too many or too few loses the whole answer. An offline repair of
the JSON turned {{mvs.spec.repair.n_scene}} of those {{mvs.spec.repair.n_raw}} answers into
scene trees (these were not checked by the viewer). This is why the final run reports strict and valid-only scores side by side and adds a
JSON-mode condition.

**Table P1. Pilot run, per model (preliminary).** {{mvs.n_tasks}} tasks, one sample each,
ordered by task success. *Valid outputs*: answers that parse and that the viewer accepts.
*F1*: how much of the drawn state is right (0 to 1). *Task success*: share of answers whose
drawn state is exactly right. *Strict*: an invalid answer counts as 0. *Valid outputs only*:
the mean over valid answers.

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

**Table P2. Pilot run by tier, all models pooled (preliminary).** *Outputs*: answers, one per
model and task. *Valid*: answers that parse and that the viewer accepts. *F1, earlier grader*:
the score under the grader used in October, for comparison. *F1* and *task success*: as in
Table P1, strict. *Requested part exactly right*: among answers to tasks whose reference marks
out a requested part against a background, the share that draw that part with exactly the
reference's atoms, representation and colour (strict).

{{include:generated/table_october_regrade.md}}

![**Figure 6. Pilot run: three scores by tier (preliminary).** Strict means over all answers of all {{oct.spec.n_models}} models. *F1*: how much of the drawn state is right. *Task success*: drawn state exactly right. *Requested part exactly right*: the residues or ligand the request is about drawn exactly as in the reference, whatever the rest of the answer shows. In the clinical tier the requested part was usually right and the whole state almost never.](generated/fig_october_regrade.svg)

**How Finding 2 changed the design.** (i) A reference now holds only what the request
states; if context is wanted, the request asks for it in words. (ii) Every task stores its
target atoms, and the target score is reported next to F1 and task success, so that scenery and
substance can no longer be confused. (iii) An attribute that the request does not state is
free (Section 3.5). (iv) The clinical tier was rebuilt: {{clin.n}} tasks on
{{clin.n_proteins}} proteins, {{clin.n_offset}} of them with a numbering offset, in place of
{{mvs.spec.regime.Clinical.n_tasks}} tasks on one protein with none.

**Finding 3: grounding packs did not help.** Appending each task's grounding pack to the
request lowered task success over all tasks from {{oct.spec.success:.1%}} to
{{oct.spec_grounded.success:.1%}}, and the number of valid answers from {{oct.spec.n_valid}} to
{{oct.spec_grounded.n_valid}}: the longer prompt produced more invalid output. On the clinical
tier, task success was {{oct.spec.clinical.success:.1%}} without the pack and
{{oct.spec_grounded.clinical.success:.1%}} with it. Finding 2 explains why the pack had little
to add: the residue was already right without it. Whether a pack helps when it holds a number
that the model cannot guess is a question for the rebuilt clinical tier (Table 9).

**Finding 4: without the format reference, no answer was valid.**
The condition with the instruction and the output rule only was run on {{mvs.bare.n_models}}
models, with and without grounding packs. None of their {{mvs.bare.n_samples}} answers was a
valid scene. For these models, knowledge of the
MolViewSpec format came from the prompt and not from training.

**Finding 5: our first call-list track did not separate models from a keyword script.** That
track had {{legacy_api.n_tasks}} hand-written tasks and a grader that compared call lists field
by field. The keyword script scored {{legacy_api.baseline_f1:.2f}} on it, and the
{{legacy_api.n_models}} models between {{legacy_api.f1_min:.2f}} and
{{legacy_api.f1_max:.2f}} (run of {{legacy_api.run}}). These numbers are the reason the track
was rebuilt; they are not results of the present benchmark.

**Finding 6: a pilot rating study, with its limits.** In October, valid scenes that scored
below 1 were also rendered and shown to the image judge (Section 5.5); a scene that the judge
called the same as the reference was counted as right in a side column, a *rescue*. Volunteers
then rated a sample of those picture pairs. In this pilot ({{pilot.n_raters}} raters, one of
them the author; {{pilot.all.n_labelled}} labelled answers on {{pilot.all.n_pairs}} image
pairs), people agreed with the judge on {{pilot.all.agreement:.0%}} of answers (Cohen's kappa
{{pilot.all.kappa:.2f}}, 95% interval {{pilot.all.kappa_lo:.2f}} to
{{pilot.all.kappa_hi:.2f}}), and confirmed {{pilot.all.rescue:.0%}}
({{pilot.all.rescue_lo:.0%}} to {{pilot.all.rescue_hi:.0%}}) of its "same" calls;
{{pilot.indep.rescue:.0%}} ({{pilot.indep.rescue_lo:.0%}} to {{pilot.indep.rescue_hi:.0%}})
without the author. Cohen's kappa is agreement beyond what chance would give: 0 is chance and
1 is perfect. Under the earlier grader, the judge's rescues changed no model's mean F1 by more than
{{mvs.spec.escalation.lift_max:.3f}}, and no result above uses them. Only
{{pilot.n_raters_passing_checks}} of the {{pilot.n_raters}} raters passes the attention-check
rule as it was written before the data were seen (at least {{pilot.check_rule:.0%}} right on
each kind of check item): the author was never shown a check item, and one volunteer answered
"can't tell" on a check, which the rule counts as a miss. The all-rater numbers therefore
depart from that rule. This pilot does not validate the image judge. It gives no measure of
agreement between people, because only {{pilot.all.pairs_two_raters}} pairs received two
labelled answers. It supports no statement about tiers or single models, and none about the
final run.

*End of the preliminary evidence.*

</div>
