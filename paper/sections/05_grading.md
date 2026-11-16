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
nothing by itself; on the wrong entry nothing can be compared and every score is 0.

On the call-list track the grader replays the calls in order, following the behaviour of PDBe
Mol\* 3.3.2, and compares the end state. Because that viewer draws the whole structure as soon
as it loads, the facts of a call-list answer are its *differences from a bare load*. Order
matters, as it does in the viewer: a later call can undo an earlier one, and the answer is
graded on where it ends. SI Section S4 lists every rule on both tracks.

### 4.2 Three scores

Each answer receives three scores. They answer different questions, and Section 4.3 shows them
parting on the running example.

**F1: how much of the drawn state is right?** *Recall* is the mean, over the reference's
facts, of how much of each fact the answer has. *Precision* is the mean, over the answer's
facts, of how much of each the reference has. F1 is their harmonic mean, from 0 to 1. For a
group of atoms, "how much" is the share of their draws that the other side also has; a draw
with the right representation and the wrong colour counts half. Missing drawing therefore
costs recall, and unrequested drawing costs precision.

**Task success: is the drawn state exactly right?** Yes if recall and precision are both 1 on
the right structure: every fact of the reference is present and the answer has no other. For a
model on a task, task success is the share of its sampled answers that are exactly right. This
is the headline score, because a viewer scene is either the one that was asked for or it is
not.

**Target score: are the requested atoms right, whatever else was drawn?** Each task stores
the atoms the request is about. The target score, from 0 to 1, compares only how those atoms
are drawn: it gives credit for each requested draw that the answer has (half credit for the
wrong colour), and takes credit away when the answer applies the same drawing to atoms outside
the target (colouring the whole chain when one residue was asked for) or wraps the target in a
representation that was not requested. Context that merely passes through the target, such as
a cartoon of the whole chain, is ignored. The target score separates "found the wrong residue"
from "found the right residue and added scenery".

When a task lists several accepted answers (Section 3.3), an answer is graded against each,
and the best result counts. The two tracks share these definitions; the arithmetic of F1
differs slightly between them (SI Section S4), and task success means the same on both.

### 4.3 The running example, graded

Figure 4 and Table 2 grade several answers to the running example. The reference draws
{{ex.wild_type}}{{ex.auth_number}} of chain {{ex.auth_chain}} as {{ex.color}} {{ex.rep}}, and
nothing else.

![**Figure 4. Drawn-state grading of three answers to the running example.** Each panel shows a stretch of chain {{ex.auth_chain}} in author numbering, the facts of the answer's drawn state, and its scores. *Recall*: share of the reference's facts that the answer has. *Precision*: share of the answer's facts that the reference has. *F1*: their harmonic mean. *Task success*: drawn state exactly right. *Target score*: the requested atoms drawn as asked, whatever else was drawn.](generated/fig_grading.svg)

**Table 2. Answers to the running example and their scores**, computed by the benchmark's
grader. *F1*: how much of the drawn state is right (0 to 1). *Task success*: the drawn state
is exactly right. *Target score*: the requested atoms are drawn as asked, whatever else was
drawn (0 to 1).

{{include:generated/table_example.md}}

Three points follow. First, an answer may name the residue in any numbering: the second row of
each track is written differently from the reference and scores the same, because it draws the
same atoms. Second, the answer that takes "75" at face value draws
{{ex.face_value_residue}}{{ex.uniprot_position}}, shares no atom with the reference, and scores
0 on all three measures. Third, the answer that finds the right residue and adds a grey
cartoon of the protein has a target score of {{ex.mvs.context.target:.2f}} but an F1 of
{{ex.mvs.context.f1:.2f}} and no task success: it drew a cartoon over the whole chain that the
request did not mention. F1 alone cannot tell this answer from one that found the
wrong residue against a correct background; the target score can.

### 4.4 Invalid output

Some answers cannot be shown at all. Every sampled answer gets one *outcome*. On the scene
track an answer is *valid* if it parses as JSON, is a scene tree, and passes the validation of
Mol\* 5.9.0 itself, run without a display. On the call-list track an answer is valid if it
parses as a JSON list that fits the call schema. An answer with an unknown call or a wrongly
typed field is counted as not valid, but it is still replayed as the viewer would treat it and
graded on the state it reaches. An answer cut off at the token limit is counted apart from a
malformed one.

Scores are averaged in three named ways.

- **Strict** (primary): every answer counts, and an answer that cannot be shown scores 0 on
  all three scores. This is what a user of the bare model would experience.
- **Valid-only**: the mean over valid answers. This separates "wrote a loadable answer" from
  "the answer is right".
- **Repaired**: a counterfactual. Each reply that is not parseable JSON is passed through an
  offline JSON repair library [@jsonrepair] and graded again. No model is called. The repaired
  score is reported beside the strict score and never replaces it.

### 4.5 How well the grader itself works

A grader that compares drawn states can still be wrong: it may fail a correct answer that is
written in an unexpected way, or pass a wrong one. We measured this with a *control set* of
{{controls.n:,}} pairs of a reference and an answer whose verdict is known from how the pair
was made (Table 3). The answer is one of three things.

- **Identical**: the reference itself. It must pass.
- **Equivalent**: the reference rewritten so that the viewer shows the same. Examples: a
  residue range as a list of residues; label numbering in place of author numbering where the
  two name the same atoms; a colour as a hexadecimal code; one component or several; on the
  call-list track, a wrong step that a later step undoes. It must pass.
- **Wrong**: an answer that shows something else. Examples: the neighbouring residue; the other
  chain; the UniProt number used as the author number on a structure where they differ; a
  nearby shade of the colour; a missing or an extra component; another copy of the ligand. It
  must fail.

A *false pass* is a wrong answer graded as a task success. A *false fail* is an identical or
equivalent answer graded as not a success.

**Table 3. Error rate of the grader on the control set.** *False pass*: wrong answers graded as
task success, out of all wrong answers. *False fail*: identical or equivalent answers graded as
not a success, out of all such answers. *Earlier grader*: the grader that this work replaces on
each track (for the scene track, a comparison of scene trees path by path; for the call-list
track, a comparison of call sequences field by field), with a score of exactly 1 read as
success.

| Track | Controls | Structures | Kinds of equivalent / wrong answer | False pass | False fail | Earlier grader: false pass | Earlier grader: false fail |
|:---|---:|---:|---:|---:|---:|---:|---:|
| Scene | {{controls.mvs.n_controls:,}} | {{controls.mvs.n_entries}} | {{controls.mvs.n_equivalent_kinds}} / {{controls.mvs.n_wrong_kinds}} | {{controls.mvs.new.false_pass}} of {{controls.mvs.new.false_pass_n}} | {{controls.mvs.new.false_fail}} of {{controls.mvs.new.false_fail_n}} | {{controls.mvs.old.false_pass}} of {{controls.mvs.old.false_pass_n}} | {{controls.mvs.old.false_fail}} of {{controls.mvs.old.false_fail_n}} ({{controls.mvs.old.false_fail_rate:.0%}}) |
| Call list | {{controls.api.n_controls}} | {{controls.api.n_entries}} | {{controls.api.n_equivalent_kinds}} / {{controls.api.n_wrong_kinds}} | {{controls.api.new.false_pass}} of {{controls.api.new.false_pass_n}} | {{controls.api.new.false_fail}} of {{controls.api.new.false_fail_n}} | {{controls.api.old.false_pass}} of {{controls.api.old.false_pass_n}} ({{controls.api.old.false_pass_rate:.0%}}) | {{controls.api.old.false_fail}} of {{controls.api.old.false_fail_n}} ({{controls.api.old.false_fail_rate:.0%}}) |

The zeros must be read with care. We corrected the grader until it agreed with every control,
so they show that the stated rules are implemented. They do not show how often a way of
writing an answer that we did not foresee is misjudged. Two things keep the control set
honest. First, the verdicts do not come from the grader. For the scene track, both scenes of a
pair were loaded in Mol\* 5.9.0 and the atoms, colours and opacities of each representation
were read back: the viewer drew the same for the must-pass pairs and something different for
the must-fail pairs in all {{controls.viewer.mvs.checked}} pairs that can be read back this way
({{controls.viewer.mvs.skipped}} pairs of kinds such as camera target and label text cannot).
For the call-list track, {{controls.viewer.api.lists}} call lists were replayed in PDBe Mol\*
3.3.2 and the end state matched the grader's replay in every case. Second, the earlier graders
give the scale of the problem that the control set detects: the scene grader used in our pilot
run failed {{controls.mvs.old.false_fail_rate:.0%}} of correct answers, and the first call-list
grader passed {{controls.api.old.false_pass_rate:.0%}} of wrong ones. SI Section S5 lists every
kind of control with its counts.

### 4.6 What is deliberately not graded

Camera position is never graded. If the request asks to focus on something, the grader compares
which residues the camera frames; if it does not, a focus in the answer is not counted. Sizes,
line widths and label styling are not graded. Two colours are the same if every channel (0 to
255) differs by at most {{colour.tolerance}}. Requests use a palette of {{colour.palette_n}}
named colours whose closest pair ({{colour.closest_pair}}) is {{colour.closest_pair_distance}}
apart, so no palette colour can pass for another, and a lighter or darker named shade is a
different colour. In the pilot run, {{colour.oct.exact:,}} of {{colour.oct.n_comparable:,}}
comparable colour values were exactly the requested colour, and none of the other
{{colour.oct.inexact}} came closer than {{colour.oct.closest_inexact}}.
