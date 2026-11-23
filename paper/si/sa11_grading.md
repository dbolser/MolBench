## S11. Grading in detail

Section S4 gives the grading rules themselves. This section gives the reasons, the counts and
the worked examples.

### S11.1 From an answer to a drawn state

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
the default, such as the background colour or spin; it is right if reference and answer have
the same setting.

Loading the right entry earns nothing by itself. On an entry that the task does not accept,
nothing can be compared, and every score is 0.

One category is a partial exception to grading on drawn state. A name-resolution task
accepts any PDB entry of the named protein, and we hold atom tables only for panel entries.
The {{corpus.mvs.resolve.n}} tasks accept {{resolve.n_accepted_entries:,}} entries in all:
their {{corpus.mvs.resolve.n}} reference entries, {{resolve.n_other_panel_entries}} further
panel entries, and {{resolve.n_accepted_outside_panel:,}} entries outside the panel. An
answer on a panel entry is graded on drawn state. An answer on an accepted entry outside the
panel has no atom table to be resolved on: its selections are compared with the reference's
as written, and all three scores of Section 4.2 come from that comparison. The common ways
of writing "the protein" pass; a correct selection that is spelled differently, for example
by chain identifier, fails. This is the *weaker rule* of the name-resolution category. The
run records for each answer whether its entry is the reference entry, so results are
reported in two rows: answers on the reference entry, and answers on any other accepted
entry, nearly all of which fall under the weaker rule (Table 8).

On the call-list track the grader replays the calls in order, following the behaviour of PDBe
Mol\* 3.3.2, and compares the drawn state that they end in. Because that viewer draws the whole
structure as soon as it loads, the facts of a call-list answer are its *differences from the
default view*. Order matters, as it does in the viewer: a later call can undo an earlier one,
and the answer is graded on where it ends. SI Section S4 lists every rule on both tracks.

### S11.2 F1 and task success

**F1: how much of the drawn state is right?** A fact is matched atom by atom against the
other drawn state. For each atom of the fact, take the share of the atom's styles that the
other drawn state also has on that atom; a style with the right representation and the wrong
colour or opacity counts half. The *fraction* of the
fact is the mean of these shares over its atoms. A cartoon counts as a style of every atom of
each residue that it traces. *Recall* is the mean of the fraction over the facts of the
reference: how much of what was wanted the answer has. *Precision* is the same over the facts
of the answer: how much of what the answer drew was wanted. F1 is the harmonic mean of recall
and precision, from 0 to 1. Missing drawing costs recall, and unrequested drawing costs
precision. Facts count equally whatever their number of atoms: one unrequested cartoon costs
the same precision on a small protein as on a large one.

On the call-list track a fact about atoms is a group of atoms that the calls changed from the
default view in the same way. Here the grader compares the final appearance of each atom as a
whole, not style by style. The rule differs because the two formats do: a scene lists the
styles that it adds to an empty screen, so styles can be matched one by one, whereas a call
changes atoms that are already drawn, and what can be compared is how each changed atom ends
up. An atom scores 1 if it ends up drawn exactly as in the other drawn
state, one half if reference and answer both changed it but to different results, and 0 if
only one of the two changed it. Example: the right residue drawn red where {{ex.color}} was
asked for is changed by both, differently, and scores {{ex.api.colour.f1:.2f}} (Table 3, row
{{ex.row.api.colour}}; SI Section S4.6). The call-list rule is more generous than the scene rule: on
the call-list track any change to the right atoms earns one half, even in the wrong
representation, where on the scene track the wrong representation earns nothing. F1, like
task success (below), is therefore not the same measure on the two tracks, and we never
compare it between them.

**Task success: is the drawn state exactly right?** For one answer, task success is yes or
no: yes if recall and precision are both 1 on an entry that the task accepts, so that every fact of the
reference is present and the answer has no other. For a model, the *task success rate* is the
mean over tasks of the share of the task's {{plan.samples}} answers that succeed. Every task
has the same number of answers, so this equals the share of all the model's answers that
succeed. This is the primary score within a track, because a viewer scene is either the one
that was asked for or it is not. Two
further summaries are used and always named: the *all-{{plan.samples}} rate*, the share of
tasks on which all {{plan.samples}} answers succeed, and *majority*, used only in the paired
analysis, where a side of a pair counts as right if at least 2 of its {{plan.samples}} answers
are (Section 5.4).

### S11.3 The target score: which atoms, which convention, which tasks

**Target score: are the requested atoms marked out exactly?** The *target*
of a task is the atoms that the request is about. For most tasks the generator stores it with
the task. In a
clinical task it is the residue of the variant. In a task that asks for a feature against a
background ("grey cartoon and the biotin in green ball-and-stick") it is the feature, here the
biotin and not the cartoon; if several features are asked for, it is all of them. In a task
with no such distinction ("the whole protein as a yellow cartoon") it is everything the
reference draws.

The counts (wanted, credit, attempted, spill, extra), the three rules for extra drawing and
the formula are in Section S4.3.

The line between rules 2 and 3 is whether the added style is confined to the target. A second
representation on the target alone is read as another answer to "how should these atoms be
drawn?", and a style that also covers other atoms as background. The line is a convention,
and it has a cost that two rows of Table 3 show: {{ex.other_rep}} added to the residue alone
is penalised (row {{ex.row.mvs.extra}}, {{ex.mvs.extra.target:.2f}}), and the same
{{ex.other_rep}} added to the residue and its two neighbours is not (row
{{ex.row.mvs.other_rep_around}}, {{ex.mvs.other_rep_around.target:.2f}}). Task success and F1
penalise both.

On the call-list track the same counts are made on the changes from the default view on the
target atoms: a style that a call adds, or a default style that it removes. Every first
request of this track asks for some change on its target, so a load with no further call is
target-right in none of the {{corpus.api.n_first_requests}} first requests (checked with the
grader). A paired request for a cartoon is no exception ("{{corpus.api.cartoon_example}}"): the
default view already draws a cartoon, but not in the requested colour, and the reference
recolours it.

A target score exists for {{corpus.n_with_target_score}} of the {{corpus.n_tasks}} tasks. For
{{corpus.n_with_target}} of them the generator stores the target. For
{{corpus.n_without_target_settings}} more, in which a first request changes a setting of the
viewer or hides something (a background colour, the water molecules), the target is
everything the reference changes. The remaining {{corpus.n_without_target_followup}} tasks
are follow-up turns whose edit takes something away, changes or restores a setting of the
whole view, or needs no change. They have no target score, and averages leave them out:
after such an edit no atoms are left that are "drawn as asked", and with everything the
reference draws as the target, the start state returned unchanged would earn nearly full
marks.

**Unrequested context: the rule on each track.** On the scene track the screen starts empty,
so anything drawn beyond the request counts against precision and task success. On the
call-list track the viewer starts with the whole structure drawn, only changes from that
default view are graded, and leaving the default view in place costs nothing. Task success is
therefore not the same test on the two tracks. The target score ignores unrequested context
on both tracks and is computed with the same counts on both; the more generous rule of the
call-list F1 (one half for any change to the right atoms) is not used for it. The verdict
*target-right* is therefore the same test on both tracks. Two consequences follow, and they
fix the primary score of each table (Table S0f). Within a track, models are ranked by the task
success rate, and the target score is reported beside it. Between the two formats, models
are compared on the pairs only, and first on whether each answer is target-right (Section
5.4).

When a task lists several accepted answers (Section 3.3), an answer is graded against each,
and the best result counts.

### S11.4 The running example, worked by hand

*The two spill rows of Table 3.* The target score can be checked by hand, in
items (one style on one atom). The target has {{ex.n_target_atoms}} atoms, so credit and
attempted are both {{ex.n_target_atoms}}. The answer draws the {{ex.color}} {{ex.rep}} on
{{ex.neighbours_n_atoms}} atoms in all (row {{ex.row.mvs.spill}}) or on all
{{ex.chain_n_atoms:,}} atom records of the author chain (row {{ex.row.mvs.spill_chain}}); the
items outside the target are spill. Target precision is therefore
{{ex.n_target_atoms}}/{{ex.neighbours_n_atoms}} = {{ex.mvs.spill.target_precision:.2f}} or
{{ex.n_target_atoms}}/{{ex.chain_n_atoms:,}} = {{ex.mvs.spill_chain.target_precision:.3f}},
target recall is 1, and their harmonic mean is {{ex.mvs.spill.target:.2f}} or
{{ex.mvs.spill_chain.target:.2f}}. On the call-list track the cartoon of the default view is
on screen in every row but row {{ex.row.api.hide_cartoon}} and costs nothing; on the scene
track the same cartoon is unrequested context (row {{ex.row.mvs.context}}).

Four points follow. First, an answer may name the residue in any numbering: rows
{{ex.row.mvs.label}} and {{ex.row.api.author}} are written differently from the reference and
score the same, because they draw the same atoms. Second, the answer that copies the "{{ex.uniprot_position}}" of
{{ex.name_in_prompt}} (rows {{ex.row.mvs.face}} and {{ex.row.api.face}}) draws
{{ex.face_value_residue}}{{ex.uniprot_position}}, shares no atom with the reference, and
receives 0 on all three scores. Third, the answer that finds the right
residue and adds a grey cartoon of the protein (row {{ex.row.mvs.context}}) has a target score of
{{ex.mvs.context.target:.2f}} but an F1 of {{ex.mvs.context.f1:.2f}} and no task success: it
drew a cartoon over the whole chain that the request did not mention. Fourth, the last two
rows show what is special to the call-list track. A call list that also recolours the
residue's own segment of the default cartoon passes because the task lists that drawn state
as a second accepted answer, not because of the F1 rule (row
{{ex.row.api.default_colour}}; Section 3.2). A call list that hides the default cartoon makes
a change that the request does not ask for: it is target-right but not a task success (row
{{ex.row.api.hide_cartoon}}).

The F1 of the answer with the added cartoon (Table 3, row {{ex.row.mvs.context}}; Figure 4,
Answer B) is worked out as follows. The answer has two facts. Fact 1 is the atoms of
{{ex.wild_type}}{{ex.auth_number}}; they carry two styles, the grey cartoon and the
{{ex.color}} {{ex.rep}}, and the reference has one of the two: one half. Fact 2 is all other
atoms of the protein; they carry only the grey cartoon, and the reference has none of it:
zero. Precision is the mean of the two, {{ex.mvs.context.precision:.2f}}. Recall is
{{ex.mvs.context.recall:.2f}}, because the reference's one fact is fully present. F1, their
harmonic mean, is {{ex.mvs.context.f1:.2f}}.

Row {{ex.row.api.hide_cartoon}} is worked out by the call-list rule of Section 4.2. The
reference has one fact, the atoms of the residue. The answer has two: the residue, and all
other atoms, on which it hid the cartoon. Reference and answer both changed the residue, but
it ends up drawn differently, because the answer also removed its cartoon: one half. Only the
answer changed the other atoms: zero. Recall is {{ex.api.hide_cartoon.recall:.2f}}, precision
is the mean of one half and zero, {{ex.api.hide_cartoon.precision:.2f}}, and F1 is
{{ex.api.hide_cartoon.f1:.2f}}. The target score stays at {{ex.api.hide_cartoon.target:.2f}}:
the {{ex.color}} {{ex.rep}} are on the residue and on no other atom, and hiding the cartoon
is a change that reaches beyond the target, which rule 3 ignores.

An F1 of {{ex.mvs.context.f1:.2f}} alone does not say what went wrong: a half-right residue
with no context could score in the same range (the right residue drawn red scores
{{ex.mvs.colour.f1:.2f}}, row {{ex.row.mvs.colour}}). The target score of {{ex.mvs.context.target:.2f}} says that the
residue is right and that the loss is unrequested context.

### S11.5 Outcomes and averages

Every answer gets one *outcome*. It is *valid*, or it is *invalid* in one of two ways that must
be kept apart: unshowable, or schema-breaking.

- **Valid.** Scene track: the answer parses as JSON, is a scene, is accepted by the
  validation of Mol\* 5.9.0 itself, run without a display, and names a structure file that
  the viewer can load. The grader decides the last point from the address alone, without
  fetching anything: the address must be that of a structure file on a site of the PDB
  archive or of the AlphaFold Protein Structure Database, in the file format that the scene
  says it parses. Call-list track: the answer parses as a JSON list that fits the *call
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

- **Strict** (the default): every answer counts. An unshowable answer scores 0; a schema-breaking
  call list keeps the scores it earns. This is what a user of a bare model, one without
  tools, would experience.
- **Valid-only**: the mean over a model's valid answers, all pooled, so a task with more
  valid answers weighs more and a task with none contributes nothing. This separates "wrote a
  loadable answer" from "the answer is right".
- **Repaired**: a counterfactual. Each answer that is not parseable JSON is passed through an
  offline JSON repair library [@jsonrepair] and graded again. No model is called. The repaired
  score is reported beside the strict score and never replaces it.

### S11.6 The control set and the check in the running viewers

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
answer that we did not foresee is misjudged. Finding such cases needs people, and is the
purpose of the rating study (Section 5.5).

**The check in the running viewers.** The verdict of a control comes from how it was made,
not from the grader. For many controls it was also checked in the viewers; this is the same
check that compares the atom tables with the viewer (Section 3.7).

- *Scene track.* Both scenes of {{controls.viewer.mvs.checked}} of the
  {{controls.mvs.n_controls:,}} controls were loaded in Mol\* 5.9.0, run without a display,
  and their drawing was read back. In every one the viewer showed the same drawing where the
  control must pass and a different one where it must fail, and the grader's resolved atoms
  were those that the viewer drew.
- *Call-list track.* A sample of {{controls.viewer.api.sample}} controls, with every kind of
  control represented, was replayed in PDBe Mol\* 3.3.2: {{controls.viewer.api.lists}} of
  their {{controls.viewer.api.sample_lists}} call lists. Each selection was compared atom for
  atom, and every list ended in the state that the grader computes.
- *Default view.* The default view after a load with no further call was compared in the
  same way for {{controls.viewer.api.bare_loads}} of the {{panel.n_pdb}} PDB entries of the
  panel.

Not checked in a viewer are {{controls.viewer.mvs.skipped}} scene controls of kinds that
cannot be read back in this way (for example the text of a label), any control
added after the read-back, the call-list controls outside the sample, and every call list
that selects by UniProt number. SI Section S5 gives the counts and says how the sample was
drawn.

The earlier graders, both our own, give the scale of the problem that the control set
detects (Table 4, last two columns). SI Section S5 lists every kind of control with its
counts.

### S11.7 What is deliberately not graded

Camera coordinates are never graded. A requested focus is graded by which residues the camera
frames; an unrequested focus in the answer is ignored. Sizes, line widths and the appearance of
labels are not graded. Two opacities count as the same if they differ by at most
{{colour.opacity_tolerance}}. Two colours count as the same if their red, green and blue values
(0 to 255) each differ by at most {{colour.tolerance}}. Requests use a palette of
{{colour.palette_n}} named colours, of which the two closest are
{{colour.closest_pair_distance}} apart, so no palette colour can pass for another. A named
lighter or darker shade of a requested colour, such as "darkred" for red, lies outside the
tolerance and counts as wrong. In the pilot run the tolerance decided no case (SI Section
S4.5).
