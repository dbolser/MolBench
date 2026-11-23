## S10. The corpus in detail

Sections S10 to S15 hold detail that the paper gives in one sentence each: rules, counts,
special cases and caveats. In these sections, a section, table, figure or box that is cited
without the letter S is one of the paper.

### S10.1 Disease proteins and the clinical tasks

**Disease proteins and variants.** The panel includes structures of
{{panel.n_disease_proteins}} human proteins in which germline missense variants cause
Mendelian disease, that is, disease caused by changes in a single gene (missense: one amino
acid is replaced by another; germline: the variant is in every cell of a person). We chose the proteins by hand, as familiar
examples that have experimental structures. For each protein, one PDB entry was then chosen
by a scripted rule that did not look at how the entry is numbered (SI Section S3). A protein
can still have tasks on more than one structure: on its chosen entry, on its predicted
structure where the panel has one, and on another panel entry that also contains it ({{clin.n_structures_two_proteins:word}}
haemoglobin entries hold both the alpha and the beta chain). In all,
{{clin.n_proteins_several_structures}} proteins have tasks on more than one structure.

**From the pool to the clinical tasks.** A clinical task asks about one variant, or a few, on
a panel structure of its protein. The generator picks the variant by seeded random choice
among the pool variants whose residue is observed in the structure (present in its
coordinates; flexible parts of a chain are often missing from them) with the amino acid that
the UniProt canonical sequence has at that position. For {{clin.n_featured_proteins}} proteins a well-known variant, named by
hand before generation, is tried first (for example the sickle-cell variant of haemoglobin
beta, p.Glu7Val; SI Section S3.2 has the list). The result is
{{clin.n}} tasks per track on {{clin.n_proteins}} proteins and {{clin.n_structures}}
structures: {{clin.n_pdb_structures}} PDB entries and the {{panel.n_alphafold}} predicted
structures. There is one PDB entry more than there are proteins, because
{{clin.n_proteins_one_pdb_entry}} proteins have tasks on one PDB entry each and the two
haemoglobin chains on {{clin.n_haemoglobin_pdb_entries:word}} between them. There are at most {{clin.max_tasks_per_structure}} tasks per track on one structure.
The other {{panel.n_disease_proteins_without_task:word}} proteins have no task, because no
variant of the pool is observed in their panel structure (SI Section S3.2).

### S10.2 The categories in detail

*Categories that differ in what the model must know.*

- **Translation.** Everything needed is in the request: the entry, the chains, the residue
  numbers, the colours. The model only has to write it in the format.
- **Structure-grounded.** The request names a feature, such as the ligand, the disulfide bonds
  (links between two cysteine residues) or the residues that hold a metal ion. The model does
  not see the file. It must either use a generic selector of the format where one fits (for
  example "ligand") or recall what the entry contains, such as the identifier of the ligand
  or the numbers of the residues. The references are computed from the entry's own records.
- **Name resolution.** The request names a protein, not an entry ("a structure of human p53
  bound to DNA"), and the model must choose an entry. Any entry on a frozen list of the PDB
  entries of that protein is accepted (SI Section S4.4 gives the rule and the date of the
  list). An answer on an accepted entry outside the structure panel is graded by a weaker
  rule (Section 4.1).
- **Clinical variant.** As in the running example: the request names a variant, and the model
  must find its residue in the structure, where its number often differs from the one in the
  name. Section 3.3.1 describes this category.

*Categories that differ in the form of the task.*

- **Interactions.** As in translation, the request states everything, so nothing more must be
  known about the structure. What differs is what must be written: single atoms are selected,
  not whole residues, and something is drawn between or around them, such as a hydrogen bond
  as a dashed line labelled with its length, with the camera centred on it.
- **Follow-up turn.** The model receives a start state, written as a scene or a call list in
  the format of its answer, and an edit request ("make the magenta chain plum"). It returns
  the complete new state. Only the resulting drawn state is graded, so an answer that makes
  the edit but drops something from the start state, such as the colour of another chain,
  fails. In {{corpus.followup.mvs.noop}} scene tasks and {{corpus.followup.api.noop}}
  call-list tasks the right answer is the start state returned unchanged. In most of these
  the edit asks for something that the start state already shows ("{{corpus.followup.noop_example}}"
  when the start state has already hidden them). In 2 scene tasks the edit asks for a spin,
  which a scene cannot express, and the request itself says to change nothing in that case.
- **Several right answers.** The request leaves one countable thing open. "Colour Lys29
  yellow" in an insulin entry with two B chains can mean either copy or both. The script lists
  every *accepted answer* (a median of {{corpus.accept.mvs.median_states:.0f}} per task on the
  scene track), and an answer that matches any one of them is right.
- **Viewer settings.** Settings that only the call-list format can express, such as the
  background colour and spin.

Name resolution and clinical variant are the *lookup categories*. In both, what the request
leaves out is one piece of information that a person would look up in a database: which entry holds the
protein, or which residue number the variant has in the entry. The model cannot look it up and
must recall it. Only these two categories have a grounding pack, in which the lookup has been
done for the model (Section 5.2).

The {{corpus.n_tasks}} tasks ({{corpus.mvs.n}} on the scene track, {{corpus.api.n}} on the
call-list track) use {{corpus.n_structures}} of the {{panel.n}} panel structures. No structure
appears in more than {{corpus.max_tasks_per_structure_tier_track}} tasks of one category and
track. The call-list track has more translation tasks than the scene track because its format
has many single-purpose calls and selectors. Of its {{corpus.api.translation.n}} translation
tasks, {{corpus.api.translation.n_call_only}} (from
{{corpus.api.translation.n_call_only_templates}} templates) exercise calls that have no
counterpart in a scene; the other {{corpus.twins.translation}} are pairs.

### S10.3 The clinical category in detail

There are {{clin.n}} clinical tasks per track, on {{clin.n_proteins}} proteins and
{{clin.n_structures}} structures. Of these, {{clin.n_one_variant}} name one variant; the other
{{clin.n_multi}} name several, up to {{clin.max_variants_per_task}}. In all, the requests
name {{clin.n_variants}} distinct variants; a variant that is asked about on two structures
(matched tasks, below) is counted once. No target residue has an insertion code.

*How variants are named.* The requests use three forms of name. Three-letter names
({{ex.hgvs}}) and one-letter names ({{ex.name_in_prompt}}) carry the prefix "p.". In this
corpus a name with "p." is always in UniProt numbering; the prefix itself does not say so.
*Traditional names* ({{ex.mature_name}}) carry no prefix and are in mature-protein numbering,
as in older literature. Names with "p." follow the protein-level style of the HGVS
nomenclature [@denDunnen2016hgvs; @hart2024hgvs], but they are not complete HGVS descriptions:
a complete description names a versioned reference sequence, and a UniProt accession, which
{{clin.n_accession_in_prompt}} requests state, is not one that HGVS accepts. ClinVar itself
states each change on a transcript, and we did not check which transcript its protein-level
name is counted on. SI Section S3.2 gives the details of both points, and Section S14.2 the
limit that follows.

The request asks for the residue in one of three wordings: "the residue it replaces", "the
residue replaced by" the variant, or "the wild-type residue at the position of" the variant.
All three mean the amino acid that the UniProt canonical sequence has at that position; the
third uses "wild-type", the usual word in structural biology, where clinical genetics would
say "reference".

*Traditional names.* A traditional name is used in {{clin.n_mature_name}} requests (for
example transthyretin V30M, which is p.Val50Met). Each of these requests says so, and says
what mature-protein numbering leaves out. One of them in full:

> *"{{clin.mature_example.prompt}}"*

In UniProt numbering this variant is {{clin.mature_example.hgvs}}. Entry
{{clin.mature_example.entry}} is numbered from the mature protein as well, so here the
printed {{clin.mature_example.number}} is the author residue number, and copying it is right.
SI Section S3.2 says what each of the {{clin.n_mature_name}} traditional names leaves out.

*Two groupings.* Each clinical task has two yes-or-no properties that matter for the results.
They are not the same property (Table 2).

- **Copying the number** (the grouping on which the question of the Introduction is
  answered). If an answer uses the number printed in the
  variant name as the author residue number, is it right? Copying is right in
  {{clin.n_face_value_right}} tasks and wrong in {{clin.n_face_value_wrong}}. The property
  describes what copying does on the scene track, where the model must give an author or a
  label number. On the call-list track the printed number can also be passed unchanged to
  the viewer's UniProt selector (Section 3.4), so results are grouped by this property on
  the scene track only (Section 6.4).
- **Offset** (reported for description only). Does the author number of the target residue differ
  from its UniProt number? An offset is present in {{clin.n_offset}} tasks
  ({{clin.offset_share:.0%}}) and absent in {{clin.n_no_offset}}. Where there is one, the
  UniProt number is always the larger, by {{clin.offset_min}} to {{clin.offset_max}}
  residues.

A task with several target residues is assigned by rule. Copying counts as right only if the
answer with every number copied is exactly right, that is, if copying is right for every named
variant. The task has an offset if any of its target residues has one. Some tasks also ask
for the helix or strand that contains the residue (helices and strands are the two common
local shapes of a protein chain; the entry records where each begins and ends). In such a
task both properties are those of the variant's residue, not of the whole helix or strand. As it turns out, all {{clin.n_multi}} tasks with several variants and all
{{clin.n_sse}} helix or strand tasks have an offset, and copying is wrong in all of them.

With a name in UniProt numbering, copying is right exactly when there is no offset. The two
groupings differ only for the {{clin.n_mature_name}} traditional names. In
{{clin.n_face_right_offset}} of them the entry is also numbered from the mature protein, so
the number in the name is the author number although the UniProt number is not. The one
remaining traditional name ({{clin.traditional_on_predicted.name}} of haemoglobin beta, which
is {{clin.traditional_on_predicted.hgvs}}) is asked on a predicted structure, which
uses UniProt numbering. There, copying the traditional number selects the wrong residue
although the target has no offset (the single task in the top-right cell of Table 2).

*Further properties.* Table S20 lists further properties of the clinical tasks. One needs a
remark. Where a request states no UniProt accession and names the variant with "p.", neither
the request nor the system prompt says which sequence the position is counted on. A reader of
a bare name with "p." would normally take it to be counted on the protein of the gene's MANE
Select transcript, the one transcript per gene that RefSeq and Ensembl jointly designate as
the default for clinical reporting [@morales2022mane]. We assume, and did not check, that
this protein is numbered as the UniProt canonical sequence is (Section S14.2).

**Table S20. Further properties of the {{clin.n}} clinical tasks.** *Tasks*: number of tasks
per track with the property. Indented rows divide the row above them. *Traditional name*: a
name in mature-protein numbering, without "p."; the request then says how the name is
numbered.

| Property of the task | Tasks | Why it matters |
|:-------------------------|--:|:--------------------------|
| The request states the UniProt accession, as the running example does | {{clin.n_accession_in_prompt}} | On the call-list track the accession can be passed on to the viewer (Section 3.4). |
|  of which: name in UniProt numbering / traditional name | {{clin.n_accession_uniprot}} / {{clin.n_accession_traditional}} | |
| The request states no accession | {{clin.n_no_accession}} | The model must know the accession to use the UniProt selector. |
|  of which: name in UniProt numbering / traditional name | {{clin.n_no_accession_uniprot}} / {{clin.n_no_accession_traditional}} | |
| The entry holds several copies of the protein, and the request says which are meant | {{clin.n_several_copies}} | The chain identifier must be right as well as the number. |
|  of which: "in every chain that has it" / one named chain ("in chain B only") | {{clin.n_every_chain}} / {{clin.n_one_chain}} | With "every chain", the target is the residue in all of those chains; an answer that draws it in one chain only is not target-right. |
| The author chain identifier differs from the label chain identifier | {{clin.n_chain_differs}} | The two numberings must not be mixed. |
| A cartoon of the structure is also asked for, in words | {{clin.n_context_cartoon}} | The reference then holds the cartoon, and on the scene track task success requires it. |
| The helix or strand that contains the residue is also asked for | {{clin.n_sse}} | The model must also know where the entry records that helix or strand to begin and end; these tasks are reported apart. |

*Matched tasks.* On each track, {{clin.n_in_pairs}} of the {{clin.n}} tasks form
{{clin.n_structure_pairs}} sets of two *matched tasks*, which ask about the same variant on
two structures of one protein. In {{clin.n_offset_pairs}} of these sets one structure has an
offset and the other, always a predicted structure, has none. Both tasks of a set name the
variant in the same form. In {{clin.n_offset_pairs_uniprot_name}} of the
{{clin.n_offset_pairs}} sets the name is in UniProt numbering, so copying is wrong on the
structure with the offset and right on the predicted structure; Section 6.4 reports these
{{clin.n_offset_pairs_uniprot_name}} sets. The eighth set uses the traditional name
{{clin.traditional_on_predicted.name}} of haemoglobin beta, and there it is the other way
round: copying is right on the PDB entry and wrong on the predicted structure. In the other 2
sets, both of p53, neither structure has an offset (the PDB entry uses UniProt numbering);
they are not reported apart.

### S10.4 The two formats in detail

The two formats differ in kind. A MolViewSpec scene [@midlik2025mvs] is *declarative*: a tree
that states what to load, which atoms form a *component* (a named set of selected atoms), and
how each component is drawn.
Nothing is on screen unless the scene says so. A call list is *imperative*: an ordered list of
calls to the PDBe Mol\* viewer, version 3.3.2 [@pdbemolstar]. The viewer starts with the whole
structure drawn in a *default view*, and each call changes that state, so order matters. The
call list is written as a JSON list in a small notation of our own, which the format guide
documents (Section 5.2). Each item names one call or setting of the viewer and its arguments,
under the names that the viewer's Python notebook widget, ipymolstar 0.1.0 [@ipymolstar],
gives them. The model does not write JavaScript or Python, and the grader follows what PDBe
Mol\* 3.3.2 does with each call.

The formats also differ in what they demand for a clinical request, and we state this openly
because it shapes the comparison. The viewer behind the call-list track can select a residue by
UniProt accession and position and does the mapping itself. A scene has no such selector: the
model must produce author or label numbers. Any selection that the format allows is accepted
if it resolves to the right atoms: author or label numbering on the scene track, and those
two or the UniProt selector on the call-list track. On the call-list side of a clinical pair,
a model can thus be right without knowing any residue number of the entry. When the request
states the accession and the name is in UniProt numbering ({{clin.n_accession_uniprot}} of
the {{clin.n}} clinical requests), the model only has to pass both on to the right call.
When no accession is stated ({{clin.n_no_accession_uniprot}}), it must also know the
accession.

The {{clin.n_mature_name}} requests with a traditional name are a separate case. Their printed
number is not the UniProt position, so the UniProt selector gives the wrong residue if the
number is passed on as printed. In {{clin.n_face_right_offset}} of them the printed number is
the entry's author number, and selecting by author number is right on either track; in the
remaining one the model must convert the number on either track. The format guide of the call-list track documents the UniProt selector, and the
guide of the scene track documents selection by author and by label numbering; neither says
how a given structure is numbered (Section 5.2).

The grader resolves the UniProt selector through the frozen mapping table. UniProt selections
on PDB entries were not replayed in the viewer, so there the agreement between grader and
viewer rests on both using SIFTS (Section S14.3).

Pairs exist in five categories: translation ({{corpus.twins.translation}}), structure-grounded
({{corpus.twins.grounded}}), clinical ({{corpus.twins.clinical}}), follow-up
({{corpus.twins.followup}}) and several right answers ({{corpus.twins.accept_set}}). The
other {{corpus.n_mvs_without_twin}} scene tasks have no partner on the call-list track. Either the
call-list format cannot draw what they ask for (a distance line, a text label, a transparent
surface), or they are name-resolution tasks, in which the model chooses the entry and the
call-list grader has no atom table for an entry outside the panel.

Pairs are compared on the target score first, because task success is not the same test in
the two formats (Section 4.2 gives the reason, Section 5.4 the analysis).

In {{corpus.twins.need_hide_toggle}} pairs the reference call list contains an extra call
that switches off part of the default view, a call that a scene never needs. All of these
are first requests, not follow-up turns. In {{corpus.twins.hide_required}} of them the request
asks for something to be shown alone, or for part of the structure to be hidden
("{{corpus.twins.hide_example}}"), and the call list must contain the call. In the other
{{corpus.twins.hide_optional}} the request asks for the whole protein as a surface or as
spacefill spheres; the reference switches off the default cartoon, and a call list that leaves
the cartoon in place is accepted as well. The paired analysis is reported with and without
these {{corpus.twins.need_hide_toggle}} pairs.

### S10.5 What a request may leave open

Requests written by people leave things unsaid, and a benchmark must decide what silence
means. We use one rule: **an attribute that the request does not state is free; one that it
states must match.** If the request gives no colour for a ligand, the grader ignores the
colour, and any colour is accepted. If the request says
"green", only green is right. Where the open point is which atoms are meant, the task lists
every accepted answer (Section 3.3, several right answers).

The same holds for the representation. On the scene track nothing is drawn unless the scene
names a representation, and every first request states one for each thing it asks to be
drawn, with one exception: {{corpus.mvs.n_representation_open}} tasks of the category with
several right answers name none for a ligand
("{{corpus.mvs.representation_open_example}}"), and they list the ligand in each
representation as an accepted answer. On the call-list track a request can state a colour
alone, for a chain or a residue: the atoms are already drawn in the default view, and the
reference only recolours them. Opacity is not covered by the rule. A reference is opaque
unless the request states an opacity, which {{corpus.n_opacity_stated}} tasks do, and an
answer that draws a requested style with another opacity earns half credit for it (Section
4.2).

The rule covers attributes of what was requested. Additions to the picture, such as a cartoon
that the request does not mention, are not covered by it; Section 4.2 says how they are
scored.

### S10.6 Set-aside structures and wording

MolBench tasks have been public since May 2026, so a model released later may have seen
earlier tasks. By *earlier* tasks and releases we mean those published before the present
corpus (the first version of the benchmark, Section 6). Two measures address this.

*Set-aside structures.* Before generation, {{corpus.heldback.n_structures}} structures were
set aside: no earlier MolBench release used them, and their tasks are reported apart. The
{{corpus.heldback.n_tasks}} tasks on them ({{corpus.heldback.share:.0%}} of the corpus) form
the *set-aside split*. The other {{corpus.public.n_tasks}} tasks sit on
{{corpus.public.n_structures}} structures, of which
{{corpus.public.n_structures_used_earlier}} appeared in earlier MolBench tasks (scene tasks
or call-list tasks of any release of the first version; its pilot run, of scene tasks alone, used
{{mvs.n_structures}}) and
{{corpus.public.n_structures_not_used_earlier}} did not.

The split compares two sets of structures. It does not compare seen tasks with unseen tasks:
nearly all tasks in both parts were generated for this version. Nor is the set-aside split a
hidden test set: the corpus was developed in a public repository, so its tasks were online
for some days before the final run. Three set-aside structures share a protein with one of
the other structures.

*How we read it.* A clearly lower score on the set-aside structures would suggest that scores
on the other structures profit from earlier tasks on them or from their being better known. A
difference near zero would not show the opposite. We report the difference with an interval
and do not test it, because the split is small (Section S14.4).

*Wording.* To measure sensitivity to wording, {{corpus.n_requests_paraphrased}} requests on
structures outside the set-aside split have, beside their original (*full*) wording, two further phrasings each, a
*terse* one and an *indirect* one, with the same reference. For example, the request "{{corpus.paraphrase_example.full}}" also exists in
a terse form ("{{corpus.paraphrase_example.terse}}") and in an indirect form
("{{corpus.paraphrase_example.indirect}}"). Of the
{{corpus.n_requests_paraphrased}} requests, {{corpus.n_paraphrased_pairs}} are pairs, so they are
{{corpus.n_tasks_paraphrased}} tasks, and two further phrasings of each give
{{corpus.n_paraphrase_files}} additional task files. These are not counted in Table 1.
