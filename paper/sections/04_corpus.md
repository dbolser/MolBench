## 3. Building the benchmark

A task is a request, a reference answer, the atoms the request is about (the *target*), and a
record of how the reference was made. No reference is written by hand. This section follows
the running example from public data to a finished task, and then describes the corpus as a
whole.

### 3.1 Frozen public data

**Structures.** All tasks draw on a fixed panel of {{panel.n}} structures: {{panel.n_pdb}} PDB
entries [@wwpdb2019] and {{panel.n_alphafold}} predicted models from the AlphaFold Protein
Structure Database [@varadi2024afdb]. {{corpus.n_structures}} of them are used in tasks; the
other one is reserved as the worked example in a prompt (Section 3.3). The panel was chosen
for coverage, not at random: small and large folds, proteins with bound small molecules, haem
groups and metal ions, proteins rich in disulfide bonds, nucleic acids, attached sugars,
membrane proteins, and entries whose functional assembly differs from the deposited model.
{{panel.n_xray}} entries were solved by X-ray crystallography, {{panel.n_cryoem}} by
cryo-electron microscopy and {{panel.n_nmr}} by nuclear magnetic resonance. The
{{panel.n_alphafold}} predicted models are of {{panel.alphafold_proteins}}; each of these
proteins also has an experimental structure in the panel, and a predicted model is numbered as
UniProt is. Every feature we claim for an entry is verified in its file by the build script,
or the build fails. In {{panel.n_offset}} structures at least one residue has an author number
that differs from its UniProt number. Entries are limited to {{panel.max_atoms:,}} atoms so
that they render quickly ({{panel.n_over_size_limit}} larger entries are kept because earlier
tasks used them). The Supporting Information (SI, Section S3) lists the panel and its
selection rule.

**Disease proteins.** {{panel.n_disease_proteins}} human disease proteins are listed by
UniProt accession. For each, one PDB entry is chosen by a scripted rule (coverage of variant
positions, then resolution; SI Section S3). Whether an entry is numbered differently from
UniProt played no part in the choice. A variant may also be asked on any other panel structure
of the same protein: {{clin.n_proteins_several_structures}} proteins have more than one
structure in the panel, counting the {{panel.n_alphafold}} predicted models. The clinical
tasks therefore sit on {{clin.n_structures}} structures.

**Variants.** We use *missense* variants only: one amino acid replaced by another. Throughout,
the *classification* of a variant means ClinVar's combined (aggregate) germline classification
on a variation record, the record whose accession begins with VCV. The list of variants was
built in three steps; the counts are of variants removed and left.

{{include:generated/table_variants.md}}

*Step 2* exists because UniProt lists a variant as pathogenic when any one submission to
ClinVar says so, whereas ClinVar's own classification combines all submitters. A candidate is
kept only if a ClinVar record that UniProt cites for it lists the same amino-acid change at
the same position and is classified "Pathogenic", "Likely pathogenic" or "Pathogenic/Likely
pathogenic". Step 2 removed {{variants.removed_share:.0%}} of the candidates, most of them
classified as conflicting or of uncertain significance. We did not compare transcripts: the
position is that of the UniProt canonical sequence, and the ClinVar record must list the
change at that position.

*Step 3* exists because a request says "the *GENE* variant ... is classified as pathogenic in
ClinVar", so the classification must rest on a record of that gene, about that one change,
with stated criteria. In step 3a the other gene is nearly always one that encodes the same
protein (*CALM2* or *CALM3* for calmodulin, *HBA2* for alpha-globin). In step 3b the record
describes two changes on one chromosome and says nothing about either alone. In step 3c no
submitter stated the criteria behind the classification.

The {{variants.n_usable:,}} variants left are the pool from which tasks are drawn. Two
decisions were made by name. One variant removed in step 3c is used all the same: lysozyme
p.Ile74Thr (I56T in the older literature), the first described cause of hereditary lysozyme
amyloidosis; it is outside the {{variants.n_usable:,}}. One variant inside the
{{variants.n_usable:,}} is never asked about, because its clinical meaning is easily misread:
APOE p.Arg154Ser, the Christchurch variant. Tasks exist for {{clin.n_proteins}} of the
{{panel.n_disease_proteins}} proteins; for the other
{{panel.n_disease_proteins_without_task}} the steps above left at most one variant, and no
task was made. The variant lists and their classifications were read from UniProt and ClinVar
on {{variants.clinvar_retrieved}}; the kind and review status of each ClinVar record were read
on {{variants.records_retrieved}}.

**Atom tables and residue mapping.** For each structure we store two frozen tables. The *atom
table* lists every atom with its chain and residue in both author and label numbering; it is
built from the deposited file and compared with what the viewer itself selects (Section 3.7).
The *mapping table* holds the SIFTS correspondence between each observed residue and its
UniProt position. Generators and graders read only these tables. Nothing is fetched while a
task is built from the tables, graded or loaded.

### 3.2 From data to a task: the running example

The clinical generator produced the running example in six steps.

1. **Variant.** From the pool it draws {{ex.gene}} {{ex.variant}} (UniProt {{ex.accession}},
   {{ex.hgvs}}; "{{ex.disease}}"; classified {{ex.clinvar_classification}}). ClinVar holds
   {{ex.n_clinvar_records}} records of this protein change, one for each DNA change that
   causes it ({{ex.clinvar_records}}). Their review status is "{{ex.clinvar_review_status}}";
   we return to what that means in Section 9.
2. **Structure.** The panel entry for {{ex.accession}} is {{ex.entry}}, human lysozyme at
   {{ex.resolution}} Å resolution.
3. **Mapping.** The mapping table says that UniProt positions
   {{ex.map_uniprot_first}}–{{ex.map_uniprot_last}} are author residues
   {{ex.map_auth_first}}–{{ex.map_auth_last}} of author chain {{ex.auth_chain}}: an offset of
   {{ex.offset}}, the length of the signal peptide. Position {{ex.uniprot_position}} is
   therefore author residue {{ex.auth_number}} (label chain {{ex.label_chain}}, label residue
   {{ex.label_number}}).
4. **Identity check.** The atom table must hold the amino acid of the reference sequence at
   that residue. It does: {{ex.wild_type}}{{ex.auth_number}}, {{ex.n_target_atoms}} atoms
   ({{ex.n_target_heavy_atoms}} heavy atoms and {{ex.n_target_hydrogens}} hydrogens, which
   this entry contains). Had the structure carried an engineered substitution there, the variant would
   not be offered for this entry.
5. **Wording.** A seeded random choice picks one of the template's three wordings, the colour
   ({{ex.color}}) and the representation ({{ex.rep}}). The request names the entry, the gene,
   the UniProt accession and the variant. It never says which residue of the entry is meant.
6. **Reference, twice.** The script writes the reference scene (author chain
   {{ex.auth_chain}}, author residue {{ex.auth_number}}, {{ex.color}} {{ex.rep}}) and the
   reference call list (load the entry; draw UniProt {{ex.accession}} position
   {{ex.uniprot_position}} as {{ex.color}} {{ex.rep}}). It then confirms that both resolve to
   the same {{ex.n_target_atoms}} atoms, and stores them as the target of both tasks. On the
   call-list track the viewer also paints the residue's stretch of the cartoon unless it is
   told not to. The request says nothing about that stretch, so both outcomes are accepted
   (SI Section S1).

The reference contains only what the request states: one residue, one representation, one
colour. It has no cartoon of the protein behind the residue, because the request does not ask
for one. Section 6.6 shows why this rule exists. SI Section S1 gives both tasks in full.

### 3.3 Eight tiers

Tasks are grouped into eight tiers by what a model must know beyond the request (Figure 2,
Table 1). The tiers are kinds of task, not steps on one scale of difficulty. Each tier has
several *templates*: a template fixes what is asked, and a seeded generator fills in the
structure, the residues, the colours and the wording. The corpus has {{corpus.n_templates}}
templates. No template supplies more than {{corpus.max_template_share_other:.0%}} of a tier's
tasks, except in the name-resolution tier (there are only five ways to name a protein) and in
the small call-list tier of requests with several right answers. SI Section S2 lists every
template with an example.

![**Figure 2. The eight tiers, with one request each.** Counts are tasks on the scene track / the call-list track; a dash means that the format cannot express the tier. Requests are quoted from the corpus. Shaded: the two *lookup tiers*, name resolution and clinical variant, in which the answer needs one fact from a database.](generated/fig_tiers.svg)

- **Translation.** Everything needed is in the request: the entry, the chains, the residue
  numbers, the colours. The model only has to write it in the format.
- **Structure-grounded.** The request names a feature, such as the ligand, the disulfide bonds
  or the residues that hold a metal ion. Its atoms must be known from the structure. References
  are read from the entry's own records.
- **Interactions.** The request names atoms and a measurement between them, such as a hydrogen
  bond drawn as a labelled line.
- **Name resolution.** The request names a protein, not an entry ("a structure of human p53
  bound to DNA"). Any entry on a frozen list of matching entries is accepted. If the model
  chooses an entry of the panel, its answer is graded on drawn state. For an accepted entry
  outside the panel we hold no atom table, and the answer's selections are compared with the
  reference's as written, so a correct answer that is spelled differently can fail there
  (Section 9). Results are reported apart for answers on the reference entry and answers on
  any other accepted entry.
- **Clinical variant.** As in the running example. There are {{clin.n}} tasks per track, on
  {{clin.n_proteins}} proteins and {{clin.n_structures}} structures. Two properties of a task
  matter for the results, and they are not the same property.
    - *Split A (primary): would an answer that copies the number in the variant name be
      right?* Yes in {{clin.n_face_value_right}} tasks, no in {{clin.n_face_value_wrong}}.
    - *Split B: does the author number of the target differ from its UniProt number?* Yes in
      {{clin.n_offset}} tasks ({{clin.offset_share:.0%}}), by {{clin.offset_min}} to
      {{clin.offset_max}} residues; no in {{clin.n_no_offset}}.
    - *Why the splits differ.* {{clin.n_mature_name}} requests use a traditional name that is
      counted along the mature protein, the form found in older literature (transthyretin
      V30M, which is p.Val50Met), and say so. In {{clin.n_face_right_offset}} of them the
      entry is numbered in the same traditional way, so the number in the name is the author
      number although the UniProt number is not. In the other
      {{clin.n_face_wrong_no_offset}} the structure is a predicted model numbered as UniProt
      is, so there the traditional number is wrong. The "yes" side of Split A is therefore
      {{clin.n_face_right_no_offset}} + {{clin.n_face_right_offset}} =
      {{clin.n_face_value_right}} tasks.
    - *Further facts.* In {{clin.n_chain_differs}} tasks the author chain identifier differs
      from the label chain identifier. {{clin.n_accession_in_prompt}} requests state the
      UniProt accession, as the running example does. {{clin.n_context_cartoon}} requests
      also ask, in words, for a cartoon of the structure. {{clin.n_sse}} ask for the helix or
      strand that contains the residue, as annotated in the entry, together with the residue.
    - *Matched tasks.* {{clin.n_in_pairs}} tasks form {{clin.n_structure_pairs}} sets of two
      *matched tasks*, which ask the same variant on two structures of one protein. In
      {{clin.n_offset_pairs}} of these sets one structure has an offset and the other, always
      a predicted model, has none.
- **Follow-up turn.** The model receives a start state and an edit request ("make the magenta
  chain plum") and returns the complete new state. Only the resulting drawn state is graded,
  so an answer that makes the edit but drops something from the start state, such as the
  colour of another chain, fails. In {{corpus.followup.mvs.noop}} scene tasks and
  {{corpus.followup.api.noop}} call-list tasks the right answer is to change nothing.
- **Several right answers.** The request leaves one countable thing open. "Colour Lys29
  yellow" in an insulin entry with two B chains can mean either copy or both. The script lists
  every *accepted answer* (a median of {{corpus.accept.mvs.median_states:.0f}} per task on the
  scene track), and an answer that matches any one of them is right.
- **Viewer settings.** Settings that only the call-list format can express, such as electron
  density maps, background and spin.

We call name resolution and clinical variant the *lookup tiers*. In both, what the request
leaves out is one fact from a database: which entry holds the protein, or which residue number
the variant has in the entry. Only these two tiers have a grounding pack (Section 5.2).

**Table 1. The corpus.** Tasks per tier and track, written as total (public + held back; Section
3.6). *Pairs*: requests posed on both tracks with the same target atoms. A dash means that the
format cannot express the tier.

{{include:generated/table_corpus.md}}

The {{corpus.n_tasks}} tasks ({{corpus.mvs.n}} scene, {{corpus.api.n}} call-list) use
{{corpus.n_structures}} of the {{panel.n}} panel structures. The one unused entry is the worked
example in the call-list prompt, which must not also be a task. No structure appears in more
than {{corpus.max_tasks_per_structure_tier_track}} tasks of one tier and track.

### 3.4 The same request in two formats

A wrong answer has two possible causes: the model did not know which atoms were meant, or it
knew and could not write them in the format. One format cannot separate the two. MolBench
therefore poses {{corpus.n_twin_pairs}} requests ({{corpus.twin_share_of_mvs:.0%}} of the scene
tasks) on both tracks, with identical wording and the same target atoms (Figure 3).

The two formats differ in kind. A MolViewSpec scene [@midlik2025mvs] is *declarative*: a tree
that states what to load, which atoms form a component, and how each component is drawn.
Nothing is on screen unless the scene says so. A call list is *imperative*: an ordered list of
calls to the PDBe Mol\* viewer, version 3.3.2 [@pdbemolstar]. The viewer starts with the whole
structure drawn in a default style, and each call changes that state, so order matters.

The formats also differ in what they demand for a clinical request, and we state this openly
because it shapes the comparison. The viewer behind the call-list track can select a residue by
UniProt accession and position and does the mapping itself. A scene has no such selector: the
model must produce author or label numbers. The running example's call-list reference uses the
UniProt selector; its scene reference uses author residue {{ex.auth_number}}. Either numbering
is accepted on either track if it resolves to the right atoms. On the call-list side of a
clinical pair, a model can thus be right without knowing any residue number: when the request
states the accession ({{clin.n_accession_in_prompt}} of the {{clin.n}} clinical requests), it
only has to pass the accession and the position on to the right call; otherwise it must also
know the accession.

![**Figure 3. One request, two formats, the same target atoms.** The scene and the call list are shown in shortened form. Below: for each model, every pair falls into one of four cells by whether each side is right. The primary comparison counts a side as right when its target score is 1; it is repeated with task success (Section 5.4). McNemar's test compares the two shaded cells, in which the model was right in one format only.](generated/fig_twins.svg)

Pairs exist in five tiers: translation ({{corpus.twins.translation}}), structure-grounded
({{corpus.twins.grounded}}), clinical ({{corpus.twins.clinical}}), follow-up
({{corpus.twins.followup}}) and several right answers ({{corpus.twins.accept_set}}).
{{corpus.n_mvs_without_twin}} scene tasks have no partner on the call-list track. Either the
call-list format cannot draw what they ask for (a distance line, a text label, a transparent
surface), or they are name-resolution tasks, in which the model chooses the entry and the
call-list grader has no atom table for an entry outside the panel.

The two formats do not treat unrequested context alike, and that decides how the pairs are
compared. A scene starts from an empty screen and has to list everything it draws, so a scene
that adds a cartoon that the request did not ask for has drawn something extra and is not
exactly right. The call-list viewer draws the whole structure as soon as it loads, so a call
list that colours one residue and leaves the rest of the default view on screen has added
nothing and is right. The default view must go only where the request says so: in
{{corpus.twins.need_hide_toggle}} pairs the request asks for something to be shown alone or to
be removed ("{{corpus.twins.hide_example}}"), and the call list must then switch off part of
the default drawing, a step that the request does not spell out and that a scene never needs.
The paired analysis is reported with and without these pairs.

Task success is therefore not the same test on the two sides of a pair. The target score is
the same test on both sides, because it asks only whether the requested atoms are drawn as
asked. The paired comparison is made on the target score first and on task success second
(Section 5.4).

### 3.5 What a request may leave open

Requests written by people leave things unsaid, and a benchmark must decide what silence
means. We use one rule: **an attribute that the request does not state is free; one that it
states must match.** If the request gives no colour for a ligand, any colour is accepted:
either the task lists the accepted answers, or a rule of the grader ignores the attribute. If
the request says "green", only green is right. The same holds for the representation.

The rule covers attributes of what was requested, not additions to it. An answer that draws
something the request does not mention, such as a cartoon of the protein behind a requested
residue, has added to the picture. It loses precision and task success, and its target score
is unaffected (Section 4.2).

### 3.6 Public and held-back tasks; wording

MolBench tasks have been public since May 2026, so a model released later may have seen
earlier tasks. Two measures address this.

*Held-back split.* {{corpus.heldback.n_structures}} structures were set aside before
generation. No public task uses them, and no MolBench task published before November 2026
used them. The {{corpus.heldback.n_tasks}} tasks on them ({{corpus.heldback.share:.0%}} of the
corpus) form the *held-back split*. The split is not a secret test set: the corpus was
developed in a public repository, so these tasks were online for some days before the final
run. Nearly all tasks in both splits are new. The split therefore does not compare seen tasks
with unseen tasks. It compares structures that earlier MolBench tasks had used with structures
that none had used. Three held-back structures share a protein with a public structure. We
report the difference between the splits with an interval and do not test it, because the
split is small (Section 9).

*Wording.* To measure sensitivity to wording, {{corpus.n_requests_paraphrased}} requests of
the public split have two further phrasings each, a terse one and an indirect one, with the
same reference. For example, the request "{{corpus.paraphrase_example.full}}" also exists in
a terse form ("{{corpus.paraphrase_example.terse}}") and in an indirect form
("{{corpus.paraphrase_example.indirect}}"). {{corpus.n_paraphrased_pairs}} of the {{corpus.n_requests_paraphrased}} requests are pairs, so
they are {{corpus.n_tasks_paraphrased}} tasks, and two further phrasings of each give
{{corpus.n_paraphrase_files}} additional task files. These are not counted in Table 1.

### 3.7 Checks on the corpus

Four checks involve no model (Figure 1, bottom row).

- **Reference against structure.** Every reference must select at least one atom, must name the
  residue that the generator intended, and must grade as exactly right against itself. Every
  accepted answer must do the same.
- **Atom tables against the viewer.** Selections were read back from the running viewers. For
  the scene track, Mol\* 5.9.0 was run without a display and asked which atoms each
  representation holds. For the call-list track, {{controls.viewer.api.lists}} call lists, a
  sample taken in turn from every kind of control (Section 4.5), were replayed in PDBe Mol\* 3.3.2 and each
  selection was compared atom for atom: all agreed. Loading a structure with no further call
  was compared in the same way for {{controls.viewer.api.bare_loads}} of the
  {{panel.n_pdb}} PDB entries of the panel (the entry reserved as a worked example was left
  out, as were the predicted models). Selections by UniProt number were not part of this
  replay (SI Section S4.8).
- **Grader against a control set.** The grader is run on {{controls.n:,}} answers whose
  verdict is known (Section 4.5).
- **Format rules.** One script validates every task file against the written task format, and
  the run does not start unless every check passes.
