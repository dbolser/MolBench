## 4. Grading on drawn state

The grader turns the reference and the answer into what the viewer would draw (for every
atom, its representations and colours) and compares the two. Each answer gets three scores:
F1 (how much of the drawing is right), task success (the drawing is exactly right) and a
target score (the requested atoms are drawn as asked, whatever else was drawn). Box 2 defines
these terms and those of the run. Sections 4.1 to 4.4 give each in full, and Section 4.5
tests the grader itself.

<div class="box">

**Box 2. Terms and notation: grading and the run.**

| Term | Meaning in this paper |
|:---------|:------------------------------|
| Style | One representation with one colour and one opacity, for example "grey cartoon, opaque". |
| Drawn state | For every atom of the structure, the set of its styles, plus a few facts about the whole scene (labels, distance lines, the atoms the camera is centred on, viewer settings such as the background colour). On the call-list track: the changes from the default view. |
| Fact | One unit of the drawn state: all atoms that carry the same set of styles form one fact; each label, each distance line and each viewer setting that differs from the default is one fact. Atoms that are not drawn belong to no fact. |
| F1 | How much of the drawn state is right, from 0 to 1, with partial credit. For each fact of the reference, take the fraction of it that the answer also draws; *recall* is the mean of these fractions. *Precision* is the same in the other direction, over the facts of the answer. F1 is the harmonic mean of the two. |
| Task success | For one answer, yes or no: the drawn state is exactly right, with nothing missing and nothing extra. The *task success rate* of a model is the share of its answers that succeed. The primary score. |
| All-{{plan.samples}} rate, majority | *All-{{plan.samples}} rate*: the share of tasks on which all {{plan.samples}} answers succeed. *Majority*: at least 2 of the {{plan.samples}} answers are right; used only for pairs. |
| Target score | From 0 to 1: are the target atoms drawn as asked, whatever else the answer drew? An answer is *target-right* when its target score is exactly 1. |
| Unrequested context | Drawing that the request did not ask for, such as a cartoon of the protein behind a requested residue. |
| Valid, invalid | An answer is *valid* if the viewer can show it as it stands; otherwise it is *invalid*, in one of two ways. An *unshowable* answer cannot be shown at all and scores 0. A *schema-breaking* call list contains parts that the viewer ignores; it is graded as the viewer would treat it but is not counted as valid (Section 4.4). |
| Call schema | The list of calls that the format guide documents, with the type of each field. A call list *fits* it if every call is on the list and every field has the documented type. |
| Strict, valid-only, repaired | Three ways to average a score (Section 4.4). *Strict* (primary): every answer counts. *Valid-only*: the mean over valid answers. *Repaired*: strict, after unparseable answers have been passed through an offline JSON repair. |
| Control, control set | A *control* is a reference and one answer whose verdict is known from how the answer was made; the *control set* is all {{controls.n:,}} of them (Section 4.5). |
| Format guide | The frozen text in the system prompt that documents the answer format (Section 5.2). |
| Grounding pack | The result of an offline lookup for one task, appended to the request in one prompting condition (Section 5.2). |
| Core models, optional models | The {{plan.n_core_models}} models that are always run, and up to {{plan.n_optional_models}} larger ones (Section 5.1). |
| Keyword script | A script that maps words of the request to fixed answers by rule and uses no model. It marks the score that needs no skill. |

</div>

### 4.1 From an answer to a drawn state

An answer is graded by what the viewer would show, not by how the answer is written. The
grader turns the reference and the answer into a *drawn state*: for every atom of the
structure, the set of its *styles* (a style is one representation with one colour and one
opacity), plus a few facts about the scene as a whole. It does so with the frozen atom tables
and with the rules of the viewer itself, which we read back from the running viewer and did not
take from documentation. Two examples of such rules: a cartoon draws only polymer residues, so
a cartoon of "everything" and a cartoon of "the polymer" are the same drawing; and a cartoon
requested for a ligand is drawn by Mol\* as ball-and-stick, and is graded as that. No browser
runs and nothing is fetched while grading.

The drawn state is cut into *facts* of equal weight. All atoms that carry the same set of
styles form one fact. "The protein as a grey cartoon, with one residue also as red
ball-and-stick" is two facts: the atoms of that residue (grey cartoon and red ball-and-stick),
and all other protein atoms (grey cartoon only). Atoms that are not drawn belong to no fact.
Each text label, each distance line and, when the request asks for a focus, the set of atoms
that the camera is centred on is a further fact. So is each viewer setting that differs from
the default, such as the background colour or spin; it is right if the other side has the
same setting. Loading the right entry earns nothing by
itself; on an entry that the task does not accept, nothing can be compared and every score is
0. One category is a partial exception to grading on drawn state: a name-resolution answer on
an accepted entry outside the structure panel has no atom table to be resolved on. Its
selections are compared with the reference's as written, and all three scores of Section 4.2
come from that comparison, so a correct answer that is spelled differently can fail (Sections
3.3 and 9.3).

On the call-list track the grader replays the calls in order, following the behaviour of PDBe
Mol\* 3.3.2, and compares the drawn state that they end in. Because that viewer draws the whole
structure as soon as it loads, the facts of a call-list answer are its *differences from the
default view*. Order matters, as it does in the viewer: a later call can undo an earlier one,
and the answer is graded on where it ends. SI Section S4 lists every rule on both tracks.

### 4.2 Three scores

Each answer receives three scores. They answer different questions, and Section 4.3 shows them
parting on the running example.

**F1: how much of the drawn state is right?** A fact is matched atom by atom. For each atom of
the fact, take the share of the atom's styles that the other side also has on that atom; a
style with the right representation and the wrong colour counts half. The *fraction* of the
fact is the mean of these shares over its atoms. A cartoon counts as a style of every atom of
each residue that it traces. *Recall* is the mean of the fraction over the facts of the
reference: how much of what was wanted the answer has. *Precision* is the same over the facts
of the answer: how much of what the answer drew was wanted. F1 is the harmonic mean of recall
and precision, from 0 to 1. Missing drawing costs recall, and unrequested drawing costs
precision. Facts count equally whatever their number of atoms: one unrequested cartoon costs
the same precision on a small protein as on a large one.

On the call-list track a fact about atoms is a group of atoms that the calls changed from the
default view in the same way. Here the grader compares the final appearance of each atom as a
whole, not style by style. An atom scores 1 if it ends up drawn exactly as on the other side,
one half if both sides changed it but to different results, and 0 if the other side left it
in the default view. Example: the right residue drawn red where {{ex.color}} was asked for is
changed on both sides, differently, and scores {{ex.api.colour.f1:.2f}} (Table 3, row
{{ex.row.api.colour}}; SI Section S4.6). This rule is more generous than the scene rule: on
the call-list track any change to the right atoms earns one half, even in the wrong
representation, where on the scene track the wrong representation earns nothing. F1, like
task success (below), is therefore not the same measure on the two tracks, and we never
compare it between them.

**Task success: is the drawn state exactly right?** For one answer, task success is yes or
no: yes if recall and precision are both 1 on an accepted structure, so that every fact of the
reference is present and the answer has no other. For a model, the *task success rate* is the
mean over tasks of the share of the task's {{plan.samples}} answers that succeed. Every task
has the same number of answers, so this equals the share of all the model's answers that
succeed. This is the primary score, because a viewer scene is either the one that was asked for or it is not. Two
further summaries are used and always named: the *all-{{plan.samples}} rate*, the share of
tasks on which all {{plan.samples}} answers succeed, and *majority*, used only in the paired
analysis, where a side of a pair counts as right if at least 2 of its {{plan.samples}} answers
are (Section 5.4).

**Target score: are the requested atoms right, whatever else was drawn?** The *target* of a
task is the atoms that the request is about. For most tasks the generator stores it with the
task. In a
clinical task it is the residue of the variant. In a task that asks for a feature against a
background ("grey cartoon and the biotin in green ball-and-stick") it is the feature, here the
biotin and not the cartoon; if several features are asked for, it is all of them. In a task
with no such distinction ("the whole protein as a yellow cartoon") it is everything the
reference draws. The target score, from 0 to 1, compares only how the target atoms are drawn.
The answer earns credit for each requested style that it has on a target atom, and half
credit for the right representation in the wrong colour. *Target recall* is that credit
divided by the number of requested styles on target atoms. *Target precision* is the same
credit divided by what the answer drew on the target plus what the first two rules below
count against it. The target score is the harmonic mean of the two (SI Section S4.3). Extra
drawing is handled by three rules.

1. *Spill.* The answer draws the requested representation on the target, in any colour, and
   draws that same style on atoms outside the target as well. This lowers the score, the more
   so the more atoms it covers. Example: the whole chain as {{ex.color}} {{ex.rep}} when one
   residue was asked for.
2. *Extra on the target.* The answer adds another representation that covers only target
   atoms. This lowers the score. Example: {{ex.other_rep}} on the residue as well as the
   requested {{ex.rep}}.
3. *Unrequested context.* Any other style that reaches beyond the target, such as a cartoon or
   a surface of the chain, or {{ex.other_rep}} on the residue and its neighbours, is ignored,
   however far it reaches and whatever its colour. It is ignored even where a surface would
   hide the target in a real picture; F1 and task success count it.

The line between rules 2 and 3 is whether the added style is confined to the target. A second
representation on the target alone is another answer to the question "how should these atoms
be drawn?", and we count it as an error on the target. A style that also covers other atoms is
read as background, which the target score is defined not to judge. The line is a convention,
and it has a cost that Table 3 shows side by side: {{ex.other_rep}} added to the residue alone
is penalised (row {{ex.row.mvs.extra}}, {{ex.mvs.extra.target:.2f}}), and the same
{{ex.other_rep}} added to the residue and its two neighbours is not (row
{{ex.row.mvs.other_rep_around}}, {{ex.mvs.other_rep_around.target:.2f}}). Task success and F1
penalise both.

An answer is *target-right* when its target score is exactly 1. The target score separates
"found the wrong residue" from "found the right residue and added context". Table 3 gives the
score of one example of each rule.

A target score exists for {{corpus.n_with_target_score}} of the {{corpus.n_tasks}} tasks. For
{{corpus.n_with_target}} of them the generator stores the target. For
{{corpus.n_without_target_settings}} more, in which a first request (not a follow-up) changes
a setting of the viewer or hides something (a background colour, the water molecules), the
target is everything the reference changes. The remaining
{{corpus.n_without_target_followup}} tasks are follow-up turns whose edit takes something
away, changes or restores a setting of the whole view, or needs no change because the start state already shows what is
asked. They have no target score, and averages of the target score leave them out. The reason
is that after such an edit no atoms are left that are "drawn as asked", and if we took
everything the reference draws as the target, the start state returned unchanged would earn
nearly full marks.

**Unrequested context: the rule on each track.** On the scene track the screen starts empty,
so anything drawn beyond the request counts against precision and task success. On the
call-list track the viewer starts with the whole structure drawn, only changes from that
default view are graded, and leaving the default view in place costs nothing. Task success is
therefore not the same test on the two tracks; the target score, which ignores unrequested
context on both, is. Two consequences follow. Within a track, models are ranked by the task
success rate, and the target score is reported beside it. Between the two formats, models are
compared on the pairs only, and first on the target score (Section 5.4).

When a task lists several accepted answers (Section 3.3), an answer is graded against each,
and the best result counts.

### 4.3 The running example, graded

Figure 4 and Table 3 grade several answers to the running example. The reference draws
{{ex.wild_type}}{{ex.auth_number}} of chain {{ex.auth_chain}} as {{ex.color}} {{ex.rep}}, and
nothing else.

![**Figure 4. Drawn-state grading of the reference and two answers to the running example.** Each panel shows a stretch of chain {{ex.auth_chain}} in author numbering, the facts of the drawn state, and the scores. *Fact*: all atoms that are drawn in the same way. *Recall*: for each fact of the reference, the fraction that the answer also draws, averaged over those facts. *Precision*: the same for the facts of the answer. *F1*: the harmonic mean of recall and precision. *Task success*: drawn state exactly right. *Target score*: the requested atoms drawn as asked, whatever else was drawn.](generated/fig_grading.svg)

**Table 3. Answers to the running example and their scores**, computed by the benchmark's
grader. Rows S1 to S10 are scenes, rows C1 to C5 call lists. *F1*: how much of the drawn state
is right (0 to 1). *Task success*: the drawn state is exactly right. *Target score*: the
requested atoms are drawn as asked, whatever else was drawn (0 to 1). *Spill*, *extra on the
target* and *context* are the three rules for extra drawing of Section 4.2. In the two spill
rows the target score can be checked by hand. The target has {{ex.n_target_atoms}} atoms, and
the answer draws the {{ex.color}} {{ex.rep}} on {{ex.neighbours_n_atoms}} atoms (row
{{ex.row.mvs.spill}}) or on all {{ex.chain_n_atoms:,}} atom records of the author chain (row
{{ex.row.mvs.spill_chain}}). Target precision is therefore
{{ex.n_target_atoms}}/{{ex.neighbours_n_atoms}} = {{ex.mvs.spill.target_precision:.2f}} or
{{ex.n_target_atoms}}/{{ex.chain_n_atoms:,}} = {{ex.mvs.spill_chain.target_precision:.3f}},
target recall is 1, and their harmonic mean is {{ex.mvs.spill.target:.2f}} or
{{ex.mvs.spill_chain.target:.2f}}. On the call-list track the
cartoon of the default view is on screen in every row and costs nothing; on the scene track
the same cartoon is unrequested context (row {{ex.row.mvs.context}}).

{{include:generated/table_example.md}}

Three points follow. First, an answer may name the residue in any numbering: rows
{{ex.row.mvs.label}} and {{ex.row.api.author}} are written differently from the reference and
score the same, because they draw the same atoms. Second, the answer that copies the "{{ex.uniprot_position}}" of
{{ex.name_in_prompt}} (rows {{ex.row.mvs.face}} and {{ex.row.api.face}}) draws
{{ex.face_value_residue}}{{ex.uniprot_position}}, shares no atom with the reference, and
receives 0 on all three scores. Third, the answer that finds the right
residue and adds a grey cartoon of the protein (row {{ex.row.mvs.context}}) has a target score of
{{ex.mvs.context.target:.2f}} but an F1 of {{ex.mvs.context.f1:.2f}} and no task success: it
drew a cartoon over the whole chain that the request did not mention.

The F1 of the answer with the added cartoon (Table 3, row {{ex.row.mvs.context}}; Figure 4,
Answer B) is worked out as follows. The answer has two facts. Fact 1 is the atoms of
{{ex.wild_type}}{{ex.auth_number}}; they carry two styles, the grey cartoon and the
{{ex.color}} {{ex.rep}}, and the reference has one of the two: one half. Fact 2 is all other
atoms of the protein; they carry only the grey cartoon, and the reference has none of it:
zero. Precision is the mean of the two, {{ex.mvs.context.precision:.2f}}. Recall is
{{ex.mvs.context.recall:.2f}}, because the reference's one fact is fully present. F1, their
harmonic mean, is {{ex.mvs.context.f1:.2f}}.

An F1 of {{ex.mvs.context.f1:.2f}} alone does not say what went wrong: a half-right residue
with no context could score in the same range (the right residue drawn red scores
{{ex.mvs.colour.f1:.2f}}, row {{ex.row.mvs.colour}}). The target score of {{ex.mvs.context.target:.2f}} says that the
residue is right and that the loss is unrequested context.

### 4.4 Valid, unshowable and schema-breaking answers

Every answer gets one *outcome*. It is *valid*, or it is *invalid* in one of two ways that must
be kept apart: unshowable, or schema-breaking.

- **Valid.** Scene track: the answer parses as JSON, is a scene, is accepted by the
  validation of Mol\* 5.9.0 itself, run without a display, and names a structure file that
  the viewer can load. Call-list track: the answer parses as a JSON list that fits the *call
  schema*: every call is one that the format guide lists, and every field has the documented
  type.
- **Unshowable** (both tracks). The answer contains no parseable JSON of the right outer shape
  or, on the scene track, is not a scene, is rejected by Mol\*, or is well formed but names a
  file that the viewer cannot load (a web page in place of a structure file, for example).
  Nothing can be shown, and the answer scores 0 on all three scores. A scene that loads a
  readable file of an entry that the task does not accept is a different case: it is valid,
  and it scores 0 because nothing can be compared (Section 4.1).
- **Schema-breaking** (call-list track only). The answer parses as a JSON list but holds an
  unknown call or a wrongly typed field. The viewer ignores such parts and carries on, and so
  does the grader: the list is replayed as the viewer would treat it and keeps the scores it
  earns. It is not counted as valid.

An answer that the provider cut off at the token limit gets the outcome of the text that
arrived, which is usually unshowable; the outcome tables count cut-off answers apart from
other invalid ones. SI Table S5 lists every outcome with its score.

Scores are averaged in three named ways.

- **Strict** (primary): every answer counts. An unshowable answer scores 0; a schema-breaking
  call list keeps the scores it earns. This is what a user of the bare model would experience.
- **Valid-only**: the mean over a model's valid answers, all pooled; a task with no valid
  answer contributes nothing. This separates "wrote a loadable answer" from "the answer is
  right".
- **Repaired**: a counterfactual. Each answer that is not parseable JSON is passed through an
  offline JSON repair library [@jsonrepair] and graded again. No model is called. The repaired
  score is reported beside the strict score and never replaces it.

### 4.5 How well the grader itself works

A grader that compares drawn states can still be wrong: it may reject a correct answer that is
written in an unexpected way, or pass a wrong one. We test this with a *control set* of
{{controls.n:,}} controls (Table 4). A control is a reference and one answer whose verdict is
known from how the answer was made. The answer is one of three things.

- **Identical**: the reference itself. It must pass.
- **Equivalent**: the reference rewritten so that the viewer shows the same. Examples: a
  residue range as a list of residues; label numbering in place of author numbering where the
  two name the same atoms; a colour as a hexadecimal code; the same atoms selected as one
  component or as several; on the
  call-list track, a wrong step that a later step undoes. It must pass.
- **Wrong**: an answer that shows something else. Examples: the neighbouring residue; the other
  chain; the UniProt number used as the author number on a structure where they differ; a
  named shade of the colour that lies outside the colour tolerance (Section 4.6); a drawn part
  that is missing or added; another copy of the ligand. It must fail.

A *false pass* is a wrong answer graded as a task success. A *false fail* is an identical or
equivalent answer graded as not a success.

The grader makes no error on the control set, and this must be read with care. We developed
the grader against the controls and corrected it until it agreed with every one. The zeros
therefore show that the stated rules are implemented and stay implemented: the control set is
run as a test on every change. They are not an estimate of how often a way of writing an
answer that we did not foresee is misjudged. That estimate needs people, and is the purpose of
the rating study (Section 5.5).

**Table 4. Error rate of the grader on the control set.** *False pass*: wrong answers graded as
task success, out of all wrong answers. *False fail*: identical or equivalent answers graded as
not a success, out of all such answers. *Earlier grader*: our own grader that this work
replaces on each track (for the scene track, a comparison of scene trees path by path; for the
call-list track, a comparison of call sequences field by field), with a score of exactly 1
read as success. *Structures*: the scene controls use all {{controls.mvs.n_entries}} structures
that tasks use. The call-list controls are built around a protein residue, so they use
{{controls.api.n_entries}}: the other {{controls.api.n_entries_without}} entries
({{controls.api.entries_without}}) hold only DNA or RNA. Of the controls,
{{controls.viewer.mvs.checked}} on the scene track and {{controls.viewer.api.sample}} on the
call-list track were also checked in the running viewers (Section 4.5).

| Track | Controls | Structures | Kinds of equivalent / wrong answer | False pass | False fail | Earlier grader: false pass | Earlier grader: false fail |
|:---|---:|---:|---:|---:|---:|---:|---:|
| Scene | {{controls.mvs.n_controls:,}} | {{controls.mvs.n_entries}} | {{controls.mvs.n_equivalent_kinds}} / {{controls.mvs.n_wrong_kinds}} | {{controls.mvs.new.false_pass}} of {{controls.mvs.new.false_pass_n}} | {{controls.mvs.new.false_fail}} of {{controls.mvs.new.false_fail_n}} | {{controls.mvs.old.false_pass}} of {{controls.mvs.old.false_pass_n}} ({{controls.mvs.old.false_pass_rate:.0%}}) | {{controls.mvs.old.false_fail}} of {{controls.mvs.old.false_fail_n}} ({{controls.mvs.old.false_fail_rate:.0%}}) |
| Call list | {{controls.api.n_controls}} | {{controls.api.n_entries}} | {{controls.api.n_equivalent_kinds}} / {{controls.api.n_wrong_kinds}} | {{controls.api.new.false_pass}} of {{controls.api.new.false_pass_n}} | {{controls.api.new.false_fail}} of {{controls.api.new.false_fail_n}} | {{controls.api.old.false_pass}} of {{controls.api.old.false_pass_n}} ({{controls.api.old.false_pass_rate:.0%}}) | {{controls.api.old.false_fail}} of {{controls.api.old.false_fail_n}} ({{controls.api.old.false_fail_rate:.0%}}) |

The verdict of a control comes from how it was made, not from the grader. For many controls
it was also checked in the viewers. On the scene track, both scenes of
{{controls.viewer.mvs.checked}} of the {{controls.mvs.n_controls:,}} controls were loaded in
Mol\* 5.9.0, and the atoms, colours and opacities of each representation were read back: in
every one the viewer showed the same drawing where the control must pass and a different one
where it must fail. On the call-list track, a sample of {{controls.viewer.api.sample}} of the
{{controls.viewer.api.n_at_check}} controls that existed at the time
({{controls.viewer.api.sample_share:.0%}}) was replayed in PDBe Mol\* 3.3.2. The sample was
drawn in rotation over the kinds of control, so that every kind is represented. Each control
has two call lists, its reference and its answer. Leaving out the
{{controls.viewer.api.skipped_uniprot}} that select by UniProt number and
{{controls.viewer.api.not_runnable}} that our replay script could not run,
{{controls.viewer.api.lists}} call lists were replayed, and every one ended in the state that
the grader computes. Not checked in a viewer are:

- {{controls.viewer.mvs.skipped}} scene controls of kinds that cannot be read back in this way
  (for example the atoms the camera is centred on, or the text of a label);
- {{controls.viewer.mvs.n_added_since}} scene controls that were added after the read-back;
- the call-list controls outside that sample, among them the
  {{controls.viewer.api.n_added_since}} that were added later, and every call list that
  selects by UniProt number.

The earlier graders give the scale of the problem that the control set detects. Both were our
own. The scene grader used in our pilot run rejected
{{controls.mvs.old.false_fail_rate:.0%}} of the correct control answers and passed
{{controls.mvs.old.false_pass_rate:.0%}} of the wrong ones; the first call-list grader
rejected {{controls.api.old.false_fail_rate:.0%}} of the correct ones and passed
{{controls.api.old.false_pass_rate:.0%}} of the wrong ones. SI Section S5 lists every kind of
control with its counts.

### 4.6 What is deliberately not graded

Camera coordinates are never graded. A requested focus is graded by which residues the camera
frames; an unrequested focus in the answer is ignored. Sizes, line widths and the appearance of
labels are not graded. Two opacities count as the same if they differ by at most
{{colour.opacity_tolerance}}. Two colours count as the same if their red, green and blue values
(0 to 255) each differ by at most {{colour.tolerance}}. We measure the distance between two
colours as the largest of these three differences. Requests use a palette of
{{colour.palette_n}} named colours. Its two closest colours ({{colour.closest_pair}}) are
{{colour.closest_pair_distance}} apart, so no palette colour can pass for another. A named
lighter or darker shade of a requested colour, such as "darkred" for red, lies outside the
tolerance and counts as wrong. In the pilot run, {{colour.oct.n_comparable:,}} colour values in
answers could be compared with a requested colour. Of these, {{colour.oct.exact:,}} were exactly
the requested colour, and each of the other {{colour.oct.inexact}} was at least
{{colour.oct.closest_inexact}} away from it, so the tolerance decided no case.
