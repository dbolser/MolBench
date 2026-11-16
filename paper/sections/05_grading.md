## 4. Grading on drawn state

### 4.1 From an answer to a drawn state

An answer is graded by what the viewer would show, not by how the answer is written. The
grader turns the reference and the answer into a *drawn state*: for every atom of the
structure, the set of its *draws* (a representation type with a colour and an opacity), plus a
few facts about the scene as a whole. It does so with the frozen atom tables and with the rules
of the viewer itself, which we read back from the running viewer and did not take from
documentation. Two examples of such rules: a cartoon draws only polymer residues, so a cartoon
of "everything" and a cartoon of "the polymer" are the same drawing; and a cartoon requested
for a ligand is drawn by Mol\* as ball-and-stick, and is graded as that. No browser runs and
nothing is fetched while grading.

The drawn state is cut into *facts* of equal weight. All atoms that carry the same set of
draws form one fact. "The protein as a grey cartoon, with one residue also as red
ball-and-stick" is two facts: the atoms of that residue (grey cartoon and red ball-and-stick),
and all other protein atoms (grey cartoon only). Each text label, each distance line and the
camera target, when the request asks for one, is a further fact. Loading the right entry earns
nothing by itself; on an entry that the task does not accept nothing can be compared and every
score is 0. One tier is a partial exception to grading on drawn state: a name-resolution
answer on an accepted entry outside the panel has no atom table to be resolved on, and is
compared as written (Sections 3.3 and 9).

On the call-list track the grader replays the calls in order, following the behaviour of PDBe
Mol\* 3.3.2, and compares the drawn state that they end in. Because that viewer draws the whole structure as soon
as it loads, the facts of a call-list answer are its *differences from a bare load*. Order
matters, as it does in the viewer: a later call can undo an earlier one, and the answer is
graded on where it ends. SI Section S4 lists every rule on both tracks.

### 4.2 Three scores

Each answer receives three scores. They answer different questions, and Section 4.3 shows them
parting on the running example.

**F1: how much of the drawn state is right?** *Recall* is the mean, over the reference's
facts, of how much of each fact the answer has. *Precision* is the mean, over the answer's
facts, of how much of each the reference has. F1 is their harmonic mean, from 0 to 1. For a
fact, which is a group of atoms drawn alike, "how much" is the share of its draws that the
other side also has; a draw with the right representation and the wrong colour counts half.
Missing drawing therefore costs recall, and unrequested drawing costs precision. Section 4.3
works one case through.

**Task success: is the drawn state exactly right?** For one answer, task success is yes or
no: yes if recall and precision are both 1 on an accepted structure, so that every fact of the
reference is present and the answer has no other. For a model, the *task success rate* is the
mean over tasks of the share of the task's {{plan.samples}} answers that succeed. This is the
primary score, because a viewer scene is either the one that was asked for or it is not. Two
further summaries are used and always named: *all-{{plan.samples}}*, the share of tasks on
which every answer succeeds, and *majority*, used only in the paired analysis, where a side of
a pair counts as right if at least two of its three answers are (Section 5.4).

**Target score: are the requested atoms right, whatever else was drawn?** Each task stores
its target, the atoms the request is about. The target score, from 0 to 1, compares only how
those atoms are drawn. It gives credit for each requested draw that the answer has, and half
credit for the right representation in the wrong colour. Extra drawing is treated by its
extent. A draw that repeats the requested drawing on atoms outside the target lowers the score
(colouring the whole chain when one residue was asked for). So does an unrequested draw that
is confined to the target atoms (sticks on the residue in addition to the requested spheres).
A draw that covers far more than the target, such as a cartoon or a surface of the whole
chain, is unrequested context and is ignored, even where it would hide the target in a real
picture; task success catches that case. An answer is *target-right* when its target score is
exactly 1. The target score separates "found the wrong residue" from "found the right residue
and added context".

**Unrequested context, stated once.** On the scene track the screen starts empty, so anything
drawn beyond the request counts against precision and task success. On the call-list track
the viewer starts with the whole structure drawn, only changes from that default view are
graded, and leaving the default view in place costs nothing (Section 3.4). The target score
ignores unrequested context on both tracks. Two consequences follow. Within a track, models
are ranked by the task success rate, and the target score is reported beside it. Between the
two formats, models are compared on the pairs only, and first on the target score
(Section 5.4).

When a task lists several accepted answers (Section 3.3), an answer is graded against each,
and the best result counts. The two tracks share these definitions; the arithmetic of F1
differs slightly between them (SI Section S4), and task success means the same on both.

### 4.3 The running example, graded

Figure 4 and Table 2 grade several answers to the running example. The reference draws
{{ex.wild_type}}{{ex.auth_number}} of chain {{ex.auth_chain}} as {{ex.color}} {{ex.rep}}, and
nothing else.

![**Figure 4. Drawn-state grading of three answers to the running example.** Each panel shows a stretch of chain {{ex.auth_chain}} in author numbering, the facts of the answer's drawn state, and its scores. *Fact*: all atoms that are drawn in the same way. *Recall*: the mean share of each of the reference's facts that the answer has. *Precision*: the mean share of each of the answer's facts that the reference has. *F1*: their harmonic mean. *Task success*: drawn state exactly right. *Target score*: the requested atoms drawn as asked, whatever else was drawn.](generated/fig_grading.svg)

**Table 2. Answers to the running example and their scores**, computed by the benchmark's
grader. *F1*: how much of the drawn state is right (0 to 1). *Task success*: the drawn state
is exactly right. *Target score*: the requested atoms are drawn as asked, whatever else was
drawn (0 to 1).

{{include:generated/table_example.md}}

Three points follow. First, an answer may name the residue in any numbering: the second row of
each track is written differently from the reference and scores the same, because it draws the
same atoms. Second, the answer that takes the "{{ex.uniprot_position}}" of
{{ex.name_in_prompt}} at face value draws {{ex.face_value_residue}}{{ex.uniprot_position}},
shares no atom with the reference, and scores 0 on all three measures. Third, the answer that
finds the right residue and adds a grey cartoon of the protein has a target score of
{{ex.mvs.context.target:.2f}} but an F1 of {{ex.mvs.context.f1:.2f}} and no task success: it
drew a cartoon over the whole chain that the request did not mention.

The F1 of that third answer is worked out as follows (Figure 4, Answer B). The answer has two
facts. Fact 1 is the atoms of {{ex.wild_type}}{{ex.auth_number}}; they carry two draws, the
grey cartoon and the {{ex.color}} {{ex.rep}}, and the reference has one of the two: one half.
Fact 2 is all other atoms of the protein; they carry only the grey cartoon, and the reference
has none of it: zero. Precision is the mean of the two, {{ex.mvs.context.precision:.2f}}.
Recall is {{ex.mvs.context.recall:.2f}}, because the reference's one fact is fully present.
F1, their harmonic mean, is {{ex.mvs.context.f1:.2f}}.

An F1 of {{ex.mvs.context.f1:.2f}} alone does not say what went wrong: a half-right residue
with no context could score in the same range (the right residue drawn red scores
{{ex.mvs.colour.f1:.2f}}). The target score of {{ex.mvs.context.target:.2f}} says that the
residue is right and that the loss is unrequested context.

### 4.4 Invalid answers

Some answers cannot be shown at all. Every answer gets one *outcome*, and two things must be
kept apart.

- An answer *cannot be shown* if it contains no parseable JSON of the right outer shape or,
  on the scene track, if it is not a scene or is rejected by the validation of Mol\* 5.9.0
  itself, run without a display. Such an answer scores 0 on all three scores.
- A call list *breaks the schema* if it parses as a JSON list but holds an unknown call or a
  wrongly typed field. The viewer ignores such parts and carries on, and so does the grader:
  the list is replayed as the viewer would treat it and keeps the scores it earns. It is not
  counted as a valid answer.

A *valid answer* is thus, on the scene track, one that Mol\* accepts and, on the call-list
track, a JSON list that fits the call schema. An answer cut off at the token limit is counted
apart from a malformed one. SI Table S4 lists every outcome with its score.

Scores are averaged in three named ways.

- **Strict** (primary): every answer counts. An answer that cannot be shown scores 0; a call
  list that breaks the schema keeps the scores it earns. This is what a user of the bare
  model would experience.
- **Valid-only**: the mean over valid answers. This separates "wrote a loadable answer" from
  "the answer is right".
- **Repaired**: a counterfactual. Each answer that is not parseable JSON is passed through an
  offline JSON repair library [@jsonrepair] and graded again. No model is called. The repaired
  score is reported beside the strict score and never replaces it.

### 4.5 How well the grader itself works

A grader that compares drawn states can still be wrong: it may fail a correct answer that is
written in an unexpected way, or pass a wrong one. We test this with a *control set* of
{{controls.n:,}} controls (Table 3). A control is a reference and one answer whose verdict is
known from how the answer was made. The answer is one of three things.

- **Identical**: the reference itself. It must pass.
- **Equivalent**: the reference rewritten so that the viewer shows the same. Examples: a
  residue range as a list of residues; label numbering in place of author numbering where the
  two name the same atoms; a colour as a hexadecimal code; one component or several; on the
  call-list track, a wrong step that a later step undoes. It must pass.
- **Wrong**: an answer that shows something else. Examples: the neighbouring residue; the other
  chain; the UniProt number used as the author number on a structure where they differ; a
  named shade of the colour that lies outside the colour tolerance (Section 4.6); a missing
  or an extra component; another copy of the ligand. It must fail.

A *false pass* is a wrong answer graded as a task success. A *false fail* is an identical or
equivalent answer graded as not a success.

The grader makes no error on the control set, and this must be read with care. We developed
the grader against the controls and corrected it until it agreed with every one. The zeros
therefore show that the stated rules are implemented and stay implemented: the control set is
run as a test on every change. They are not an estimate of how often a way of writing an
answer that we did not foresee is misjudged. That estimate needs people, and is the purpose of
the rating study (Section 5.5).

**Table 3. Error rate of the grader on the control set.** *False pass*: wrong answers graded as
task success, out of all wrong answers. *False fail*: identical or equivalent answers graded as
not a success, out of all such answers. *Earlier grader*: the grader that this work replaces on
each track (for the scene track, a comparison of scene trees path by path; for the call-list
track, a comparison of call sequences field by field), with a score of exactly 1 read as
success.

| Track | Controls | Structures | Kinds of equivalent / wrong answer | False pass | False fail | Earlier grader: false pass | Earlier grader: false fail |
|:---|---:|---:|---:|---:|---:|---:|---:|
| Scene | {{controls.mvs.n_controls:,}} | {{controls.mvs.n_entries}} | {{controls.mvs.n_equivalent_kinds}} / {{controls.mvs.n_wrong_kinds}} | {{controls.mvs.new.false_pass}} of {{controls.mvs.new.false_pass_n}} | {{controls.mvs.new.false_fail}} of {{controls.mvs.new.false_fail_n}} | {{controls.mvs.old.false_pass}} of {{controls.mvs.old.false_pass_n}} ({{controls.mvs.old.false_pass_rate:.0%}}) | {{controls.mvs.old.false_fail}} of {{controls.mvs.old.false_fail_n}} ({{controls.mvs.old.false_fail_rate:.0%}}) |
| Call list | {{controls.api.n_controls}} | {{controls.api.n_entries}} | {{controls.api.n_equivalent_kinds}} / {{controls.api.n_wrong_kinds}} | {{controls.api.new.false_pass}} of {{controls.api.new.false_pass_n}} | {{controls.api.new.false_fail}} of {{controls.api.new.false_fail_n}} | {{controls.api.old.false_pass}} of {{controls.api.old.false_pass_n}} ({{controls.api.old.false_pass_rate:.0%}}) | {{controls.api.old.false_fail}} of {{controls.api.old.false_fail_n}} ({{controls.api.old.false_fail_rate:.0%}}) |

Two things keep the control set honest. First, the verdicts do not come from the grader. For
the scene track, the two scenes of each control were loaded in Mol\* 5.9.0 and the atoms,
colours and opacities of each representation were read back. This was done on the control set
as it then stood, {{controls.viewer.mvs.n_at_check:,}} scene controls. For
{{controls.viewer.mvs.checked}} of them the drawing can be read back, and in all
{{controls.viewer.mvs.checked}} the viewer drew the same for the controls that must pass and
something different for the controls that must fail. The other
{{controls.viewer.mvs.skipped}} are of kinds that cannot be read back this way, such as camera
target and label text. {{controls.viewer.mvs.n_added_since}} scene controls added since then
have not been read back in the viewer. For the call-list track, the call lists of a sample of
controls ({{controls.viewer.api.lists}} lists) were replayed in PDBe Mol\* 3.3.2, and the
state they ended in matched the grader's replay in every case. Second, the earlier graders
give the scale of the problem that the control set detects: the scene grader used in our pilot
run failed {{controls.mvs.old.false_fail_rate:.0%}} of correct control answers, and the first
call-list grader passed {{controls.api.old.false_pass_rate:.0%}} of wrong ones. SI Section S5
lists every kind of control with its counts.

### 4.6 What is deliberately not graded

Camera position is never graded. If the request asks to focus on something, the grader compares
which residues the camera frames; if it does not, a focus in the answer is not counted. Sizes,
line widths and label styling are not graded. Two colours count as the same if their red, green and
blue values (0 to 255) each differ by at most {{colour.tolerance}}. We measure the distance
between two colours as the largest of these three differences. Requests use a palette of
{{colour.palette_n}} named colours. Its two closest colours ({{colour.closest_pair}}) are
{{colour.closest_pair_distance}} apart, so no palette colour can pass for another, and a
lighter or darker named shade is a different colour. In the pilot run, {{colour.oct.exact:,}}
of {{colour.oct.n_comparable:,}} comparable colour values were exactly the requested colour,
and each of the other {{colour.oct.inexact}} was at least {{colour.oct.closest_inexact}} away
from it, so the tolerance decided no case.
