## 4. Grading on drawn state

The grader turns the reference and the answer into what the viewer would draw and compares
the two. SI Sections S4 and S11 give every rule.

### 4.1 From an answer to a drawn state

A *style* is one representation with one colour and one opacity, for example "grey cartoon,
opaque". The *drawn state* of an answer is, for every atom of the structure, the set of its
styles, plus a few things about the scene as a whole: text labels, distance lines, the atoms
that the camera is centred on, and viewer settings such as the background colour. The
grader computes it from the frozen atom tables and from the rules of the viewer itself,
which we read back from the running viewer and did not take from documentation. No browser
runs and nothing is fetched while an answer is graded; only the separate check that a
scene is valid, made before grading, runs the viewer (Section 4.4).

The drawn state is cut into *facts* of equal weight. All atoms that carry the same set of
styles form one fact. "The protein as a grey cartoon, with one residue also as red
ball-and-stick" is two facts: the atoms of that residue, and all other protein atoms. Each
label, each distance line and each setting that differs from the default is a further fact.
Atoms that are not drawn belong to no fact.

On the call-list track the grader replays the calls in order, as PDBe Mol\* 3.3.2 would
execute them. Because that viewer draws the whole structure as soon as it loads, the facts
of a call list are its *changes from the default view*.

One category is a partial exception to grading on drawn state. A name-resolution task accepts any PDB
entry of the named protein ({{resolve.n_accepted_entries:,}} entries over the
{{corpus.mvs.resolve.n}} tasks), and we hold atom tables only for panel entries. For an
answer on an accepted entry outside the panel the grader has no atoms to resolve, so it
compares the answer's selections with the reference's as text; a correct selection that is
spelled differently (by chain identifier, for example) fails. We call this the *text
rule*. An answer on an entry that the task does not accept scores 0 (Table 8).

### 4.2 Three scores

**Task success: is the drawn state exactly right?** For one answer, task success is yes or
no: yes if every fact of the reference is fully present and the answer has no other. The
*task success rate* of a model is the share of its answers that succeed.

**Target score: are the requested atoms marked out exactly?** The *target* of a task is the
atoms that the request is about: in a clinical task, the residue of the variant; in a
request for a feature against a background ("grey cartoon and the biotin in green
ball-and-stick"), the feature; where there is no such distinction, everything that the
reference draws. The target score, from 0 to 1, is how exactly the answer marks out the
target. It is 1, and the answer is *target-right*, when three things hold: the target
atoms carry the requested style; no other atom carries that style; and no drawing in
another representation is confined to the target atoms. Any other drawing, such as a cartoon of the
protein, is ignored.

The target score is the harmonic mean of a *target recall* and a *target precision*, counted
in *items* (one style on one atom), not in facts as F1 is. Target recall is the share of the requested items that the answer has, with
half credit for the right representation in another colour or opacity. Precision depends
on what the answer drew beyond the request, which is of three kinds (rows of Table 3 in
parentheses).

- *Spill*: the style that marks the target, repeated on atoms outside it
  ({{ex.row.mvs.spill}}, {{ex.row.mvs.spill_chain}}). It lowers target precision.
- *Extra*: another representation confined to the target atoms ({{ex.row.mvs.extra}}:
  {{ex.n_target_atoms}} credited items of {{ex.n_target_atoms_twice}} drawn, precision
  {{ex.mvs.extra.target_precision:.2f}}). It lowers target precision.
- *Unrequested context*: any other style that reaches beyond the target, such as a cartoon
  of the protein ({{ex.row.mvs.context}}, {{ex.row.mvs.other_rep_around}}). It is not
  counted.

Target precision divides the credit counted for target recall by everything that the answer drew to mark the
target: its items of the requested representation on the target, plus its spill and extra
items (formula in SI Section S4.3).

The line between extra and context is a convention:
{{ex.other_rep}} added to the target residue alone lowers the target score to
{{ex.mvs.extra.target:.2f}} (row {{ex.row.mvs.extra}}), while the same {{ex.other_rep}} on
the residue and its two neighbours is context and leaves the score at
{{ex.mvs.other_rep_around.target:.2f}} (row {{ex.row.mvs.other_rep_around}}; SI Section
S11.3 gives the reason). {{corpus.n_without_target_followup}} follow-up tasks, among them
both sides of {{corpus.twins.n_without_target}} pairs, have no target score and are left out of every mean of it: their
edit takes something away, changes a setting of the whole view, or needs no change, so no atoms
are "drawn as asked" afterwards (SI Section S11.3).

**F1: how much of the drawn state is right?** F1, from 0 to 1, gives partial credit. It is
the harmonic mean of *recall*, the mean over the facts of the reference of the fraction
that the answer also draws, and *precision*, the same over the facts of the answer. A style
with the right representation and the wrong colour or opacity counts half. On the call-list track an
atom's changed appearance is compared as one unit, not style by style, so any change to the right atoms earns one half, even in the wrong representation, which
earns nothing on the scene track (SI Section S11.2). Where a task lists several accepted answers, an answer is graded against each, and
the best result counts.

**Which score is primary.** Within a track, the primary score is the task success rate,
strict (Section 4.4), because a viewer scene is either the one that was asked for or it is
not. Between the two formats (Table 9a) and for copying against mapping (Table 10), it is
the target score. F1 is reported for partial credit and is never primary. The target score
is used between the formats because task success and F1 are not the same tests on the two
tracks. On
the scene track the screen starts empty, so anything drawn beyond the request costs
precision and task success. On the call-list track only changes from the default view are
graded, and leaving the default view in place costs nothing. Track totals are therefore not
compared on these two scores; the target score is computed with the same counts on both
tracks.

### 4.3 The running example, graded

Figure 4 and Table 3 grade several answers to the running example. The reference draws
{{ex.wild_type}}{{ex.auth_number}} of chain {{ex.auth_chain}} as {{ex.color}} {{ex.rep}}, and
nothing else.

![**Figure 4. Drawn-state grading of the reference and two answers to the running example.** Top: the three drawings as Mol\* 5.9.0 renders them, from one camera. The reference and Answer A look equally plausible: nothing in either picture says which residue it is. Below, each panel shows a stretch of chain {{ex.auth_chain}} in author numbering, the facts of the drawn state, and the scores. *Fact*: all atoms that are drawn in the same way. *Recall*: for each fact of the reference, the fraction that the answer also draws, averaged over those facts. *Precision*: the same for the facts of the answer. *F1*: the harmonic mean of recall and precision. *Task success* and *target score* as in Table 3; the target score ignores the cartoon of Answer B. Recall and precision here are those of F1; the target score has its own, counted per item (Section 4.2).](generated/fig_grading.svg)

**Table 3. Answers to the running example and their scores**, computed by the benchmark's
grader. *F1* (0 to 1): how much of the drawn state is right. *Task success*: the drawn
state is exactly right. *Target score* (0 to 1): how exactly the answer marks out the
requested atoms; any other drawing, such as a cartoon of the protein, is ignored. *Spill*,
*extra on the target* and *context*: the three kinds of drawing beyond the request (Section
4.2).

{{include:generated/table_example.md}}

Three points follow. First, an answer may name the residue in any numbering: rows
{{ex.row.mvs.label}} and {{ex.row.api.author}} are written differently from the reference
and draw the same atoms, so they score the same. Second, the answer that copies the
"{{ex.uniprot_position}}" of {{ex.name_in_prompt}} (rows {{ex.row.mvs.face}} and
{{ex.row.api.face}}) draws {{ex.face_value_residue}}{{ex.uniprot_position}}, shares no atom
with the reference, and receives 0 on all three scores. Third, the answer that finds the
right residue and adds a grey cartoon of the protein (row {{ex.row.mvs.context}}) has a
target score of {{ex.mvs.context.target:.2f}} but an F1 of {{ex.mvs.context.f1:.2f}} and no
task success. That F1 alone does not say what went wrong (the right residue drawn red
scores {{ex.mvs.colour.f1:.2f}}, row {{ex.row.mvs.colour}}); the target score says that the
residue is right and the loss is unrequested context (SI Section S11.4 works every score by
hand).

### 4.4 Valid, unshowable and schema-breaking answers

An answer is *valid* if it obeys the answer format and the viewer can show it. On the scene
track this is decided in a separate step before grading: the scene must pass the validation
of Mol\* 5.9.0 itself, run in a browser without a display, and must name a structure file
that can be loaded, which is decided from the address alone, with nothing fetched. On the
call-list track a valid answer is a JSON list in which every call is documented in the
format guide, has its required fields, and gives each field a value of the documented
kind. An invalid answer is
one of two things. An *unshowable* answer cannot be shown at all:
it holds no parseable JSON of the right outer shape (a scene, or a list of calls) or, on the
scene track, is rejected by the viewer or names a file that cannot be loaded. It scores 0 on
all three scores. A
*schema-breaking* answer, possible only on the call-list track, is a parseable list with an
unknown call, a missing field or a wrongly typed value, for example. The viewer ignores such parts and
carries on, so even under strict the list keeps the score that its replay earns, but it is
not counted as valid (SI Table S5).

Scores are averaged in three named ways. *Strict*, the default: every answer counts, which
is what a user of a model without tools would experience. *Valid-only*: the mean over a
model's valid answers, which separates "wrote a loadable answer" from "the answer is
right". *Repaired*: strict, after an offline library [@jsonrepair] has repaired each answer that is
not parseable JSON; it never replaces the strict score.

### 4.5 How well the grader itself works

A grader on drawn state can still reject a correct answer that is written in an unexpected
way, or pass a wrong one. We test this with a *control set* of
{{controls.n:,}} controls (Table 4). A control is a reference and one answer whose verdict
is known from how the answer was made: the reference itself (*identical*), the reference
rewritten so that the viewer shows the same (*equivalent*; label numbering in place of
author numbering, for example), or an answer that shows something else (*wrong*; the
UniProt number used as the author number, for example). A *false pass*
is a wrong answer graded as a task success. A *false fail* is an identical or equivalent
answer graded as not a success.

**Table 4. Error rate of the grader on the control set.** *False pass* and *false fail* as
defined above, each out of all answers of its kind. *Earlier grader*: our own grader that this
work replaces on each track; both compared the text of answers. The
{{controls.api.n_entries_without:word}} entries that hold only DNA or RNA have no call-list
control, because each call-list control is built around a protein residue (SI Section S5).

| Track | Controls | Structures | Kinds of equivalent / wrong answer | False pass | False fail | Earlier grader: false pass | Earlier grader: false fail |
|:---|---:|---:|---:|---:|---:|---:|---:|
| Scene | {{controls.mvs.n_controls:,}} | {{controls.mvs.n_entries}} | {{controls.mvs.n_equivalent_kinds}} / {{controls.mvs.n_wrong_kinds}} | {{controls.mvs.new.false_pass}} of {{controls.mvs.new.false_pass_n}} | {{controls.mvs.new.false_fail}} of {{controls.mvs.new.false_fail_n}} | {{controls.mvs.old.false_pass}} of {{controls.mvs.old.false_pass_n}} ({{controls.mvs.old.false_pass_rate:.0%}}) | {{controls.mvs.old.false_fail}} of {{controls.mvs.old.false_fail_n}} ({{controls.mvs.old.false_fail_rate:.0%}}) |
| Call list | {{controls.api.n_controls:,}} | {{controls.api.n_entries}} | {{controls.api.n_equivalent_kinds}} / {{controls.api.n_wrong_kinds}} | {{controls.api.new.false_pass}} of {{controls.api.new.false_pass_n}} | {{controls.api.new.false_fail}} of {{controls.api.new.false_fail_n}} | {{controls.api.old.false_pass}} of {{controls.api.old.false_pass_n}} ({{controls.api.old.false_pass_rate:.0%}}) | {{controls.api.old.false_fail}} of {{controls.api.old.false_fail_n}} ({{controls.api.old.false_fail_rate:.0%}}) |

The grader makes no error on the control set, and this must be read with care. We developed
the grader against the controls and corrected it until it agreed with every one. The zeros
show that the stated rules are implemented and stay implemented, since the control set is
run as a test on every change. They do not estimate how often a way of writing an answer
that we did not foresee is misjudged. Finding such cases needs people, and is the purpose of
the rating study (Section 5.5).

**Agreement with the viewers.** On the scene track, the
reference and the answer of {{controls.viewer.mvs.checked}} controls were each loaded in
Mol\* 5.9.0 and read back: the viewer always agreed with the verdict of the control and
drew the atoms that the grader resolves. On the call-list track, a sample of
{{controls.viewer.api.sample}} controls holds {{controls.viewer.api.sample_lists}} call
lists (a reference and an answer each). Of these, {{controls.viewer.api.lists}} were
replayed in PDBe Mol\* 3.3.2, and every one ended in the state that the grader computes;
the other {{controls.viewer.api.lists_not_replayed}} are untested:
{{controls.viewer.api.skipped_uniprot}} select by UniProt number and
{{controls.viewer.api.lists_other_not_replayed:word}} could not be run by our replay of local files. Also not checked in a viewer: controls of kinds that cannot be read back (the
text of a label, for example) and call-list controls outside the sample (SI Sections S5
and S11.6).

### 4.6 What is deliberately not graded

Camera coordinates, sizes, line widths and the appearance of labels are not graded; a
requested focus is graded by which residues the camera frames. Colours and opacities are
compared within a small tolerance, under which no colour of the request palette can pass
for another (SI Section S11.7).
