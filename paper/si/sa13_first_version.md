## S13. The first version of the benchmark: pilot findings and errors

### S13.1 The six findings of the pilot runs in full

MolBench has had two versions, and this paper names them in one way throughout. The *first
version* is the benchmark as it was public from May 2026 until the present corpus replaced
it. At the time of its last run it had a corpus of {{mvs.n_tasks}} scene
tasks on {{mvs.n_structures}} structures, {{legacy_api.n_tasks}} hand-written call-list
tasks, and two graders that compared text (Section 4.5). Two of its runs are used in this
paper: one of the call-list tasks in July 2026, and one of the scene tasks in October 2026,
which we call the *pilot run*. The *present version* is the benchmark of Sections 3 and 4.

Section 6.6 of the paper gives Findings 1 and 2 and names the others. All six follow, as
they stood in the paper before it was shortened.

**Everything in this section is preliminary.** Findings 1 to 4 come from a pilot run of
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
from {{oct.spec.f1_min:.2f}} to {{oct.spec.f1_max:.2f}} (Table S21, columns *Valid answers*
and *F1, strict*). The two are nearly proportional: the Pearson correlation between a
model's share of valid answers and its strict F1 is r = {{oct.spec.r_valid_f1:.2f}}
({{oct.spec.n_models}} models). With the strict task success rate, by which Table S21 is
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

**Table S21. Pilot run, per model (preliminary).** The run had {{mvs.n_tasks}} tasks and one
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
{{oct.spec.clinical.n}} answers (Table S22, Figure 6). The natural reading is that finding the
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
drew the right residue" is therefore a statement about drawing, not about mapping. Table S23
(rows 1 and 2) says what replaced both.

**Table S22. Pilot run by category, all models pooled (preliminary).** *Answers*: one per model
and task. *Valid*: answers that parse and that the viewer accepts. *F1, earlier grader*: the
score under the grader used in October, for comparison. *F1* and *task success rate*: as in
Table S21, strict, over all answers of the row. *Requested part exactly right*: this column has its
own denominator, given in each cell. Among answers to tasks whose reference marks out a
requested part against a background, it is the share that draw that part with exactly the
reference's atoms, representation and colour (an unshowable answer counts as wrong). It is the
forerunner of the target score of Section 4.2: the pilot tasks stored no target atoms, so the
requested part is taken from the reference. The first-version corpus had too few tasks in
three of its categories to show them apart, so they are pooled in one row. The last cell of
the row *All* pools the three cells above it.

{{include:generated/table_october_regrade.md}}

Figure 6 of the paper shows the three scores of Table S22 by category.

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

### S13.2 Nine errors in the first version and what replaced each

The first version of MolBench (defined in Section 6) was wrong in nine ways that we know of. Table S23 lists each error, how
we found out, and what replaced it in the present version, because each error is one that
another benchmark of this kind could make.

**Table S23. Nine errors in the first version of MolBench and what replaced each in the
present version.**
*Where*: the sections that give the numbers behind the row.

| Row | What was wrong | How we found out | What replaced it | Where |
|--:|:--------|:------|:--------|:----|
| 1 | Our clinical references drew a cartoon that no request asked for, and we read the low score that followed as a difficulty of finding the residue. | A breakdown of where valid answers lost their points (Section 6.6, Finding 2). | A reference holds only what the request states. If context is wanted, the request asks for it in words. Every task stores its target where it has one, and the target score is reported beside task success in Tables 6 to 10. | Sections 3.2, 4.2; 6.6, Finding 2 |
| 2 | The clinical category could not test the mapping: all its tasks sat on one protein whose structure uses UniProt numbering. | The same analysis. | {{clin.n}} tasks on {{clin.n_proteins}} proteins and {{clin.n_structures}} structures; in {{clin.n_offset}} tasks the target has an offset, and results are grouped by whether copying the number in the variant name is right (it is wrong in {{clin.n_face_value_wrong}}). | Section 3.3.1; 6.6, Finding 2 |
| 3 | "Pathogenic" was taken from a secondary source: we first took the variants that UniProt lists as pathogenic. | A check of each candidate against the ClinVar records that UniProt cross-references. For {{variants.removed_share:.0%}} of the candidates none of these records gives the same amino-acid change a pathogenic or likely pathogenic aggregate classification, and ClinVar's aggregate classification of some variants named in tasks of the first version is "conflicting classifications of pathogenicity". | A variant is used only if ClinVar holds a record of that gene and that one change with a pathogenic or likely pathogenic classification and stated criteria (one exception, SI Section S3.2). The dates are stored. | Section 3.1; SI Section S3.2 |
| 4 | Both graders compared text: scene trees path by path, call sequences field by field. They rejected correct answers that were merely written differently, both passed some wrong ones (the scene grader {{controls.mvs.old.false_pass_rate:.0%}}, the call-list grader {{controls.api.old.false_pass_rate:.0%}}), and on the call-list track a keyword script scored close to the models. | The control set. | Both tracks are graded on drawn state, and the control set is run as a test on every change. | Section 4.5, Table 4; SI Section S13.1, Finding 5 |
| 5 | Hand-written call-list tasks had errors: label numbers where author numbers were meant, and one task that was the worked example of the prompt. | A check of those references against the structures. | Every reference is generated; a sample of references is replayed in the viewer itself; and the entry used for the worked example of both system prompts is excluded from the corpus. | Sections 3.2, 3.7 |
| 6 | Some requests had no single answer. A request to highlight "all pathogenic residues" of one protein resolved to far more residues than any user means; "show me lysozyme" was graded against one arbitrary view. | Reading the references. | Clinical requests name each variant. Requests with a countable ambiguity have their own category, with every accepted answer listed. Open-ended requests are left out. | Sections 3.3, S14.1 |
| 7 | Raters could not see what they were rating. A single highlighted residue on a whole complex was a few pixels wide, and a volunteer flagged a reference as wrong when it was only unreadable. A volunteer also found references in which two cartoons overlapped. | The trial of the rating study. | Pictures are framed on the target atoms from one shared camera. The overlapping references were corrected. The next study completes two ratings of a picture comparison before it opens new ones. | Section 5.5; SI Section S13.1, Finding 6 |
| 8 | The pilot run collected one answer per task on {{mvs.n_structures}} structures, with a short limit on the length of an answer and no record of how often an answer was cut off. | Planning the final run. | {{plan.samples}} answers per task, {{corpus.n_structures}} structures, a limit of {{plan.max_tokens:,}} tokens, and the provider's reason for the end of each answer archived. | Sections 5.3, 5.4 |
| 9 | The prompts taught answers that the graders marked wrong, and other faults of the same kind (below). | Four reviews of the benchmark by language models before the final run. | Each finding was fixed in the generator or the grader and is now covered by an automated test and by a new kind of control. Both prompt examples are graded by the benchmark's own grader as a test. | Sections 3.1, 4.5; SI Section S5 |

Row 9 needs more words than a table cell holds. Before the final run, the benchmark was
reviewed four times by language-model reviewers, each given one role (structural biologist,
clinical geneticist, benchmark methodologist, tester of the grader). The reviewers wrote
natural answers by hand and graded them, and we reproduced each finding before acting on it.
Four examples: the worked example of each prompt was written in a way that the references,
or many generated tasks, did not accept; a residue named by UniProt number on a predicted
structure was scored as selecting nothing; and a scene that named a file which the viewer
cannot load was graded as a success. The same reviews found clinical requests whose
"pathogenic" record belonged to another gene or to two variants taken together (SI Section
S3.2).
