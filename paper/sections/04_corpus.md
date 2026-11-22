## 3. Building the benchmark

A task is a request, a reference answer, the atoms the request is about (the *target*), and a
record of how the reference was made. No reference is written by hand. This section follows
the running example from public data to a finished task, and then describes the corpus as a
whole.

### 3.1 Frozen public data

**Structures.** All tasks use a fixed *structure panel* of {{panel.n}} structures:
{{panel.n_pdb}} PDB entries [@wwpdb2019] and {{panel.n_alphafold}} predicted structures from
the AlphaFold Protein Structure Database [@varadi2024afdb]. One PDB entry is reserved as the
worked example in a prompt, so tasks use {{corpus.n_structures}}. The panel was chosen for
coverage, not at random: proteins alone, with bound small molecules or metal ions, with DNA or
RNA, with attached sugars, and membrane proteins. {{panel.n_xray}} entries were solved by X-ray
crystallography, {{panel.n_cryoem}} by cryo-electron microscopy and {{panel.n_nmr}} by nuclear
magnetic resonance. The {{panel.n_alphafold}} predicted structures are of
{{panel.alphafold_proteins}}; each of these proteins also has an experimental structure in the
panel, and a predicted structure is numbered as UniProt is. In {{panel.n_offset}} structures at
least one residue has an offset: its author number differs from its UniProt number. Every
feature that we claim for an entry is verified in its file by the build script, or the build
fails. The Supporting Information (SI, Section S3) lists the panel, its features and its
selection rule.

**Disease proteins and variants.** The panel includes structures of
{{panel.n_disease_proteins}} human disease proteins. For each protein, one PDB entry was chosen
by a scripted rule that did not look at how the entry is numbered (SI Section S3). We use
*missense* variants only: one amino acid replaced by another. A variant enters the pool if
UniProt lists it as pathogenic or likely pathogenic and ClinVar's own aggregate classification
agrees, on a record that is about that gene and that one change and that states its criteria.
Of {{variants.n_candidates:,}} candidates, {{variants.n_usable:,}} pass:
{{variants.n_removed_by_clinvar}} fail the first test and {{variants.n_second_pass_removed}}
the second. SI Section S3.2 gives the filter step by step, with the dates on which the data
were read and two variants that were handled individually.

**From the pool to the clinical tasks.** A clinical task asks about a variant of the pool on a
panel structure of its protein: the chosen entry, or another panel structure that holds the
protein. The generator picks the variant by seeded random choice among those whose residue is
observed in the structure with the amino acid of the reference sequence; for a few proteins a
well-known variant is tried first. At most {{clin.max_tasks_per_structure}} clinical tasks per
track sit on one structure. Tasks exist for {{clin.n_proteins}} of the
{{panel.n_disease_proteins}} proteins; for the other
{{panel.n_disease_proteins_without_task}} the filter left at most
{{variants.max_usable_per_protein_without_task}} variant, and we made no task. The
{{clin.n_proteins}} proteins give tasks on {{clin.n_structures}} structures:
{{clin.n_pdb_structures}} PDB entries and the {{panel.n_alphafold}} predicted structures.
{{clin.n_proteins_several_structures}} proteins have tasks on more than one structure, and
{{clin.n_structures_two_proteins}} haemoglobin entries serve two proteins each, because they
hold both the alpha and the beta chain.

**Atom tables and residue mapping.** For each structure we store two frozen tables. The *atom
table* lists every atom record of the first coordinate set of the file, with its chain and
residue in both author and label numbering. It includes alternate conformers
({{panel.n_with_alternate_conformers}} structures have them) and hydrogens
({{panel.n_with_hydrogens}} structures); a selection of a residue takes all of its atom
records, as the viewer does. An author residue number is used together with its insertion code
where there is one ({{panel.feature.insertion-codes}} entries have them). The atom table is
built from the file and compared with what the viewer itself selects (Section 3.7). The
*mapping table* holds the SIFTS correspondence between each observed residue and its UniProt
position. Generators and graders read only these tables. Nothing is fetched while a task is
built from the tables, graded or loaded.

### 3.2 From data to a task: the running example

The clinical generator produced the running example in six steps.

1. **Variant.** From the pool it picks {{ex.gene}} {{ex.variant}} (UniProt {{ex.accession}},
   {{ex.hgvs}}). ClinVar holds {{ex.n_clinvar_records}} records of this protein change, one for
   each DNA change that causes it. Both are classified as {{ex.clinvar_classification}}, with
   the review status "{{ex.clinvar_review_status}}": one laboratory submitted the
   classification and stated its criteria, and no second submitter or expert panel has
   confirmed it.
2. **Structure.** The panel entry for {{ex.accession}} is {{ex.entry}}, human lysozyme.
3. **Mapping.** The mapping table says that UniProt positions
   {{ex.map_uniprot_first}}–{{ex.map_uniprot_last}} are author residues
   {{ex.map_auth_first}}–{{ex.map_auth_last}} of author chain {{ex.auth_chain}}: an offset of
   {{ex.offset}}, the length of the signal peptide. Position {{ex.uniprot_position}} is
   therefore author residue {{ex.auth_number}} (label chain {{ex.label_chain}}, label residue
   {{ex.label_number}}).
4. **Identity check.** The atom table must hold the amino acid of the reference sequence at
   that residue. It does: {{ex.wild_type}}{{ex.auth_number}}, {{ex.n_target_atoms}} atoms. Had
   the protein in the entry carried another amino acid there, the variant would not be offered
   for this entry.
5. **Wording.** A seeded random choice picks one of the template's three wordings, the colour
   ({{ex.color}}) and the representation ({{ex.rep}}). The request names the entry, the gene,
   the UniProt accession and the variant. It never says which residue of the entry is meant.
6. **Reference, twice.** The script writes the reference scene (author chain
   {{ex.auth_chain}}, author residue {{ex.auth_number}}, {{ex.color}} {{ex.rep}}) and the
   reference call list (load the entry; draw UniProt {{ex.accession}} position
   {{ex.uniprot_position}} as {{ex.color}} {{ex.rep}}). It then confirms that both resolve to
   the same {{ex.n_target_atoms}} atoms, and stores them as the target of both tasks.

One detail of the call-list viewer belongs here. It starts with the whole protein drawn as a
cartoon (Section 3.4), and a colouring call also recolours the residue's own segment of that
cartoon unless an option switches this off. The request says nothing about the cartoon, so the
call-list task accepts both results: the segment unchanged, or the segment recoloured (SI
Section S1).

The reference contains only what the request states: one residue, one representation, one
colour. It has no cartoon of the protein behind the residue, because the request does not ask
for one. Section 6.6 shows why this rule exists. SI Section S1 gives both tasks in full.

### 3.3 Eight categories of task

Tasks are grouped into eight *categories* by what a model must know beyond the request (Figure
2, Table 1). The categories are kinds of task, not steps on one scale of difficulty. Each
category has several *templates*: a template fixes what is asked, and a seeded generator fills
in the structure, the residues, the colours and the wording. The corpus has
{{corpus.n_templates}} templates. No template supplies more than
{{corpus.max_template_share_other:.0%}} of a category's tasks, except in name resolution (there
are only five ways to name a protein) and in the small call-list category of requests with
several right answers. SI Section S2 lists every template with an example.

![**Figure 2. The eight categories of task, with one request each.** Counts are tasks on the scene track / the call-list track; a dash means that the format cannot express the category. Requests are quoted from the corpus. Shaded: the two *lookup categories*, name resolution and clinical variant, in which the answer needs one fact that a person would look up in a database and that the model must recall.](generated/fig_tiers.svg)

- **Translation.** Everything needed is in the request: the entry, the chains, the residue
  numbers, the colours. The model only has to write it in the format.
- **Structure-grounded.** The request names a feature, such as the ligand, the disulfide bonds
  (links between two cysteine residues) or the residues that hold a metal ion. The model does
  not see the file. It must either use a generic selector of the format where one fits (for
  example "ligand") or recall what the entry contains, such as the identifier of the ligand
  or the numbers of the residues. The references are computed from the entry's own records.
- **Interactions.** The request names atoms and a measurement between them, such as a hydrogen
  bond drawn as a labelled line.
- **Name resolution.** The request names a protein, not an entry ("a structure of human p53
  bound to DNA"). Any entry on a frozen list of matching entries is accepted. If the model
  chooses an entry of the structure panel, its answer is graded on drawn state. For an
  accepted entry outside the panel we hold no atom table, and the answer's selections are
  compared with the reference's as written, so a correct answer that is spelled differently
  can fail there (Section 9.3). Table 8 reports answers on the reference entry and answers on
  any other accepted entry in separate rows.
- **Clinical variant.** As in the running example: the request names a variant, and the model
  must find its residue in the structure. Section 3.3.1 describes this category.
- **Follow-up turn.** The model receives a start state, written as a scene or a call list in
  the format of its answer, and an edit request ("make the magenta chain plum"). It returns
  the complete new state. Only the resulting drawn state is graded, so an answer that makes
  the edit but drops something from the start state, such as the colour of another chain,
  fails. In {{corpus.followup.mvs.noop}} scene tasks and {{corpus.followup.api.noop}} call-list
  tasks the right answer is to change nothing.
- **Several right answers.** The request leaves one countable thing open. "Colour Lys29
  yellow" in an insulin entry with two B chains can mean either copy or both. The script lists
  every *accepted answer* (a median of {{corpus.accept.mvs.median_states:.0f}} per task on the
  scene track), and an answer that matches any one of them is right.
- **Viewer settings.** Settings that only the call-list format can express, such as the
  background colour and spin.

Name resolution and clinical variant are the *lookup categories*. In both, what the request
leaves out is one fact that a person would look up in a database: which entry holds the
protein, or which residue number the variant has in the entry. The model cannot look it up and
must recall it. Only these two categories have a grounding pack, in which the lookup has been
done for the model (Section 5.2).

**Table 1. The corpus.** Tasks per category and track, written as total (public + held back;
Section 3.6). *Pairs*: requests posed on both tracks with the same target atoms. A dash means
that the format cannot express the category.

{{include:generated/table_corpus.md}}

The {{corpus.n_tasks}} tasks ({{corpus.mvs.n}} on the scene track, {{corpus.api.n}} on the
call-list track) use {{corpus.n_structures}} of the {{panel.n}} panel structures. No structure
appears in more than {{corpus.max_tasks_per_structure_tier_track}} tasks of one category and
track. The call-list track has more translation tasks than the scene track because its format
has many single-purpose calls and selectors: {{corpus.api.translation.n_call_only_templates}}
templates ({{corpus.api.translation.n_call_only}} tasks) exercise calls that the scene
templates have no counterpart for, and the other {{corpus.twins.translation}} tasks are pairs.

#### 3.3.1 The clinical category

There are {{clin.n}} clinical tasks per track, on {{clin.n_proteins}} proteins and
{{clin.n_structures}} structures. {{clin.n_one_variant}} of them name one variant; the
others name several, up to {{clin.max_variants_per_task}}. No target residue has an insertion code.

*Traditional names.* {{clin.n_mature_name}} requests use a traditional name, counted along the
mature protein, the form found in older literature (transthyretin V30M, which is p.Val50Met).
Each of these requests says so. One of them in full:

> *"{{clin.mature_example.prompt}}"*

*Two groupings.* Each clinical task has two yes-or-no properties that matter for the results.
They are not the same property (Table 2).

- **Copying the number** (the primary grouping). If an answer uses the number printed in the
  variant name as the author residue number, is it right? Copying is right in
  {{clin.n_face_value_right}} tasks and wrong in {{clin.n_face_value_wrong}}.
- **Offset** (a descriptive grouping). Does the author number of the target residue differ
  from its UniProt number? {{clin.n_offset}} tasks ({{clin.offset_share:.0%}}) have an offset,
  of {{clin.offset_min}} to {{clin.offset_max}} residues; {{clin.n_no_offset}} have none.

**Table 2. The two groupings of the {{clin.n}} clinical tasks, crossed.** *Copying the number*:
an answer that uses the number printed in the variant name as the author residue number is
right, or wrong. *Offset*: the author number of the target residue differs from its UniProt
number, or does not.

{{include:generated/table_clinical_groupings.md}}

With a name in UniProt numbering, copying is right exactly when there is no offset. The two
groupings differ only for the {{clin.n_mature_name}} traditional names. In
{{clin.n_face_right_offset}} of them the entry is numbered in the same traditional way, so the
number in the name is the author number although the UniProt number is not. In the other
{{clin.n_face_wrong_no_offset}} the traditional name is asked on a predicted structure, which
is numbered as UniProt is, so there the traditional number is wrong.

*Further properties.* In {{clin.n_chain_differs}} tasks the author chain identifier differs
from the label chain identifier. {{clin.n_accession_in_prompt}} requests state the UniProt
accession, as the running example does. {{clin.n_context_cartoon}} requests also ask, in words,
for a cartoon of the structure. {{clin.n_sse}} ask for the helix or strand that contains the
residue (the two common local shapes of a protein chain, as recorded in the entry) together
with the residue; they are reported apart.

*Matched tasks.* On each track, {{clin.n_in_pairs}} of the {{clin.n}} tasks form
{{clin.n_structure_pairs}} sets of two *matched tasks*, which ask the same variant on two
structures of one protein. In {{clin.n_offset_pairs}} of these sets one structure has an offset
and the other, always a predicted structure, has none. Table 10 reports these
{{clin.n_offset_pairs}} sets.

### 3.4 The same request in two formats

A wrong answer has two possible causes: the model did not know which atoms were meant, or it
knew and could not write them in the format. One format cannot separate the two. MolBench
therefore poses {{corpus.n_twin_pairs}} requests ({{corpus.twin_share_of_mvs:.0%}} of the scene
tasks) on both tracks, with identical wording and the same target atoms (Figure 3).

The two formats differ in kind. A MolViewSpec scene [@midlik2025mvs] is *declarative*: a tree
that states what to load, which atoms form a component, and how each component is drawn.
Nothing is on screen unless the scene says so. A call list is *imperative*: an ordered list of
calls to the PDBe Mol\* viewer, version 3.3.2 [@pdbemolstar]. The viewer starts with the whole
structure drawn in a *default view*, and each call changes that state, so order matters.

The formats also differ in what they demand for a clinical request, and we state this openly
because it shapes the comparison. The viewer behind the call-list track can select a residue by
UniProt accession and position and does the mapping itself. A scene has no such selector: the
model must produce author or label numbers. The running example's call-list reference uses the
UniProt selector; its scene reference uses author residue {{ex.auth_number}}. Either numbering
is accepted on either track if it resolves to the right atoms. On the call-list side of a
clinical pair, a model can thus be right without knowing any residue number of the entry. When
the request states the accession ({{clin.n_accession_in_prompt}} of the {{clin.n}} clinical
requests), it only has to pass the accession and the position on to the right call; otherwise
it must also know the accession. The {{clin.n_mature_name}} requests with a traditional name
are an exception: their number is not the UniProt position, so the model must convert it on
either track.

The grader resolves the UniProt selector through the frozen mapping table. The viewer reads
the same SIFTS mapping from the structure file that PDBe distributes. We did not replay
UniProt selections on PDB entries in the viewer (Section 3.7), so for these entries the
agreement between grader and viewer rests on both using SIFTS.

![**Figure 3. One request, two formats, the same target atoms.** The scene and the call list are shown in shortened form. Below: for each model, every pair falls into one of four cells by whether each side is right. The primary comparison counts a side as right when at least two of its three answers are *target-right*, that is, have a target score of exactly 1 (the requested atoms drawn as asked, whatever else was drawn); it is repeated with task success in place of the target score (Section 5.4). For a request with a traditional variant name the number must be converted on either track. McNemar's test compares the two shaded cells, in which the model was right in one format only.](generated/fig_twins.svg)

Pairs exist in five categories: translation ({{corpus.twins.translation}}), structure-grounded
({{corpus.twins.grounded}}), clinical ({{corpus.twins.clinical}}), follow-up
({{corpus.twins.followup}}) and several right answers ({{corpus.twins.accept_set}}).
{{corpus.n_mvs_without_twin}} scene tasks have no partner on the call-list track. Either the
call-list format cannot draw what they ask for (a distance line, a text label, a transparent
surface), or they are name-resolution tasks, in which the model chooses the entry and the
call-list grader has no atom table for an entry outside the panel.

Task success is not the same test on the two sides of a pair, because a scene starts from an
empty screen and the call-list viewer starts with the structure drawn. Pairs are therefore
compared on the target score first (Section 4.2 gives the rule, Section 5.4 the analysis).

A call list has to remove the default view only when the request says so. In
{{corpus.twins.need_hide_toggle}} pairs the request asks for something to be shown alone or to
be removed ("{{corpus.twins.hide_example}}"). There the call list must issue an extra call that
switches off part of the default view, a call that a scene never needs. The paired analysis is
reported with and without these pairs.

### 3.5 What a request may leave open

Requests written by people leave things unsaid, and a benchmark must decide what silence
means. We use one rule: **an attribute that the request does not state is free; one that it
states must match.** If the request gives no colour for a ligand, any colour is accepted, by a
rule of the grader that ignores an unstated colour or representation. If the request says
"green", only green is right. Where the open point is which atoms are meant, the task lists
every accepted answer (Section 3.3, several right answers).

The rule covers attributes of what was requested. Additions to the picture, such as a cartoon
that the request does not mention, are not covered by it; Section 4.2 says how they are
scored.

### 3.6 Public and held-back tasks; wording

MolBench tasks have been public since May 2026, so a model released later may have seen
earlier tasks. Two measures address this.

*Held-back split.* {{corpus.heldback.n_structures}} structures were set aside before
generation: no earlier MolBench release used them, and no task of the public split uses them.
The {{corpus.heldback.n_tasks}} tasks on them ({{corpus.heldback.share:.0%}} of the corpus) form
the *held-back split*; the other tasks form the *public split*. The name needs one warning: the
held-back tasks are themselves public. The corpus was developed in a public repository, so they
were online for some days before the final run, and the split is not a hidden test set. What
the split can show is limited. Nearly all tasks in both splits were generated for this version
and appear in no earlier release, so it does not compare seen tasks with unseen tasks. It
compares two sets of structures: the {{corpus.public.n_structures}} of the public split, of
which {{corpus.public.n_structures_used_earlier}} appeared in earlier MolBench tasks and
{{corpus.public.n_structures_not_used_earlier}} did not, and the
{{corpus.heldback.n_structures}} held-back ones, of which none did. Three held-back structures
share a protein with a public structure. We report the difference between the splits with an
interval and do not test it, because the split is small (Section 9.4).

*Wording.* To measure sensitivity to wording, {{corpus.n_requests_paraphrased}} requests of
the public split have two further phrasings each, a terse one and an indirect one, with the
same reference. For example, the request "{{corpus.paraphrase_example.full}}" also exists in
a terse form ("{{corpus.paraphrase_example.terse}}") and in an indirect form
("{{corpus.paraphrase_example.indirect}}"). {{corpus.n_paraphrased_pairs}} of the
{{corpus.n_requests_paraphrased}} requests are pairs, so they are
{{corpus.n_tasks_paraphrased}} tasks, and two further phrasings of each give
{{corpus.n_paraphrase_files}} additional task files. These are not counted in Table 1.

### 3.7 Checks on the corpus

Four checks involve no model (Figure 1, bottom row).

- **Reference against structure.** Every reference must select at least one atom, must name the
  residue that the generator intended, and must grade as exactly right against itself. Every
  accepted answer must do the same.
- **Atom tables against the viewer.** Selections were read back from the running viewers. For
  the scene track, Mol\* 5.9.0 was run without a display and asked which atoms each
  representation holds. For the call-list track, {{controls.viewer.api.lists}} call lists,
  taken from every kind of control in rotation (Section 4.5), were replayed in PDBe Mol\*
  3.3.2 and each selection was compared atom for atom: all agreed. The default view after a
  load with no further call was compared in the same way for
  {{controls.viewer.api.bare_loads}} of the {{panel.n_pdb}} PDB entries of the panel (the entry
  reserved as a worked example was left out, as were the predicted structures). Selections by
  UniProt number were not part of this replay (SI Section S4.8).
- **Grader against a control set.** The grader is run on {{controls.n:,}} answers whose
  verdict is known (Section 4.5).
- **Format rules.** One script validates every task file against the written task format, and
  the run does not start unless every check passes.
