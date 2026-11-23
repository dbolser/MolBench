## 3. Building the benchmark

A task is a request on one track, a reference answer, a record of how the reference was
made and, for most tasks, the atoms that the request is about (the *target*). No reference
is written by hand. Box 1 defines the terms that carry the results; SI
Section S0 is the full glossary.

<div class="box">

**Box 1. Terms.** *Model* always means a language model.

| Term | Meaning in this paper |
|:---------|:------------------------------|
| Author numbering | The chain names and residue numbers chosen by the depositors of a structure. Papers and most viewers show these. |
| Label numbering | The chain names and residue numbers assigned by the archive: 1, 2, 3 … along the molecule that was studied. |
| UniProt numbering | The position of a residue in UniProt's canonical sequence of the protein, counted from its first residue (the initiator methionine included). A variant name with the prefix "p." ({{ex.name_in_prompt}}, or {{ex.hgvs}}) is in this numbering here. |
| Traditional name | A variant name from older literature, without "p.", numbered from the first residue of the *mature protein*: the protein after the cell has cut off its leading segment ({{ex.mature_name}} for {{ex.name_in_prompt}}). |
| Offset | For one residue, its UniProt number minus its author number ({{ex.uniprot_position}} − {{ex.auth_number}} = {{ex.offset}} in the running example). A residue *has an offset* when the two differ. |
| Copying the number | Using the number printed in a variant name as the author residue number. Copying is *right* in a task if the answer written in this way is exactly right, and *wrong* otherwise. |
| Scene, call list | The two answer formats. A *scene* (MolViewSpec) states what to load and draw; nothing is on screen unless the scene says so. A *call list* is an ordered list of calls to the PDBe Mol\* viewer, which starts from a *default view*: the whole structure, with the polymer chains as a cartoon (a ribbon that traces each chain). |
| Track | One of the two halves of the benchmark: *scene track* and *call-list track*, named after the answer format. |
| Pair, side | A *pair* is one request posed on both tracks, with the same target atoms. A *side* is one of its two tasks. |
| Target | The atoms that the request is about (Section 4.2). |

</div>

### 3.1 Frozen public data

**Structures.** All tasks use a fixed *structure panel* of {{panel.n}} structures:
{{panel.n_pdb}} PDB entries [@wwpdb2019] and {{panel.n_alphafold}} predicted structures from
the AlphaFold Protein Structure Database [@varadi2024afdb; @jumper2021alphafold], which use
UniProt numbering. One
entry is reserved for the worked example of the system prompts, so tasks use
{{corpus.n_structures}}. The panel was chosen by hand for coverage, not at random. In {{panel.n_offset}} of the {{panel.n}} structures at least one residue
has an offset. Every feature that we claim for a structure is verified in its file by the
build script (SI Section S3.1).

**Variants.** The panel includes structures of {{panel.n_disease_proteins}} human proteins in which germline *missense* variants (one amino acid replaced by another;
germline: present in every cell of a person) cause single-gene disease.
UniProt lists {{variants.n_candidates:,}} such variants of these proteins as pathogenic or
likely pathogenic. We keep a variant only if it has a *qualifying record*: a ClinVar
variation record, cross-referenced by UniProt, that meets four conditions. It lists the same
amino-acid change at the same position; its classification is pathogenic, likely pathogenic
or pathogenic/likely pathogenic; it is a record of the gene named in the request and of that
one change alone; and its review status is not "no assertion criteria provided". This
leaves a pool of {{variants.n_usable:,}} variants, from which the generator draws: the
clinical tasks name only {{clin.n_variants}} variants, on {{clin.n_proteins}} of the
{{panel.n_disease_proteins}} proteins. SI Section S3.2 gives the filter step by step, two
exceptions made by hand, the proteins without a task, and what a request says about the
classification.

**Atom tables and residue mapping.** For each structure we freeze two tables: an *atom table*
of every atom record of the file, with its chain and residue in author and in label
numbering, and a *mapping table* with the SIFTS correspondence [@dana2019sifts; @pdbekb2020;
@pdbekb2022] between each residue and its UniProt position. Files are read with GEMMI
[@wojdyr2022gemmi]. Generators and graders read only these tables; nothing is fetched while a
task is built, graded or loaded.

### 3.2 From data to a task: the running example

The clinical generator produced the running example in six steps.

1. **Variant.** From the pool it picks the *{{ex.gene}}* variant {{ex.name_in_prompt}}
   (UniProt {{ex.accession}}). Through UniProt's cross-references we found
   {{ex.n_clinvar_records}} ClinVar records of this change, both classified as
   {{ex.clinvar_classification}} (SI Section S1).
2. **Structure.** The panel entry for this protein is {{ex.entry}}, human lysozyme.
3. **Mapping.** The mapping table says that UniProt positions
   {{ex.map_uniprot_first}}–{{ex.map_uniprot_last}} are author residues
   {{ex.map_auth_first}}–{{ex.map_auth_last}} of chain {{ex.auth_chain}}: an offset of
   {{ex.offset}}, the length of the signal peptide that the cell cuts off. Position
   {{ex.uniprot_position}} is therefore author residue {{ex.auth_number}}.
4. **Identity check.** The atom table must hold, at that residue, the amino acid that the
   UniProt sequence has at the position. It does: {{ex.wild_type}}{{ex.auth_number}}, with
   {{ex.n_target_atoms}} atom records ({{ex.n_target_heavy_atoms}} non-hydrogen atoms and
   {{ex.n_target_hydrogens}} hydrogens; the entry is at {{ex.resolution}} Å resolution).
   Otherwise the variant would not be offered for this entry.
5. **Wording.** A seeded random choice picks one of the template's wordings, the colour
   ({{ex.color}}) and the representation ({{ex.rep}}). The request never says which residue
   of the entry is meant.
6. **Reference, twice.** The script writes the reference scene (chain {{ex.auth_chain}},
   author residue {{ex.auth_number}}, {{ex.color}} {{ex.rep}}) and the reference call list
   (load the entry; draw UniProt {{ex.accession}} position {{ex.uniprot_position}} as
   {{ex.color}} {{ex.rep}}). The {{ex.uniprot_position}} is correct there: the call-list
   viewer can select by UniProt position and converts it itself, which a scene cannot do
   (Section 3.4). Both references must resolve to the same {{ex.n_target_atoms}} atoms,
   which are stored as the target of both tasks.

The reference contains only what the request states: one residue, one representation, one
colour, and no cartoon of the protein behind it. Section 6.6 shows why this rule exists. On
the call-list track a colouring call also recolours the residue's segment of the default
cartoon unless an option switches this off; the request is silent about the cartoon, so the
task accepts both results (SI Section S1).

### 3.3 Eight categories of task

Tasks are grouped into eight *categories* (Figure 2, Table 1). Four differ in what the model
must know beyond the request: nothing (*translation*), what the structure contains
(*structure-grounded*), which entry holds a protein (*name resolution*), or which residue
number a variant has in the structure (*clinical variant*). In the last two, the *lookup
categories*, the missing piece is one that a person would look up in a database and that the
model must recall. The other four differ in the form of the task: *interactions*,
*follow-up turn*, *several right answers* and *viewer settings*; Table 1 says what each
asks. Each category has several *templates*; a seeded generator fills in the structure, the
residues, the colours and the wording (SI Section S2 lists the {{corpus.n_templates}}
templates, and SI Section S10.2 describes each category in full).

![**Figure 2. The eight categories of task, with one request each.** Counts are tasks on the scene track / the call-list track; a dash means that the category has no task on that track. Requests are quoted from the corpus; a long one is cut short. A *het group* is a molecule in the entry that is not part of a polymer chain, such as a bound small molecule; *C-alpha* is the central carbon atom of an amino acid. In the example for several right answers, 4INS has a Lys29 in each of two chains, and the request does not say which is meant. Left column: the four categories that differ in what the model must know. Right column: the four that differ in the form of the task. Framed in blue: the two lookup categories.](generated/fig_tiers.svg)

**Table 1. The corpus.** Tasks per category and track, written as total (a + b): b tasks on the
{{corpus.heldback.n_structures}} *set-aside structures*, which no earlier release of the
benchmark used (Section 3.6), and a tasks on the remaining {{corpus.public.n_structures}}. *Pairs*: requests posed on both tracks. A dash means that the category has no task on
that track: the format cannot express what is asked or, for name resolution, the call-list
grader has no atom table for an entry outside the panel.

{{include:generated/table_corpus.md}}

#### 3.3.1 The clinical category

Each track has {{clin.n}} clinical tasks, on {{clin.n_structures}} structures. A request names its variant in UniProt numbering, with
the prefix "p.", or, in {{clin.n_mature_name}} requests, by a traditional name, in which
case the request says that the name is in mature-protein numbering and what that numbering
leaves out. {{clin.n_accession_in_prompt}} requests state the UniProt accession, as the
running example does; the other {{clin.n_no_accession}} do not, and neither the request nor
the system prompt then says which sequence a "p." position is counted on. A name with "p."
follows the style of the HGVS nomenclature for variants [@denDunnen2016hgvs; @hart2024hgvs]
but is not a complete description in it (SI Section S10.3).

Two yes-or-no properties of a clinical task matter for the results, and they are not the
same property (Table 2).

- **Copying the number** (Box 1) is right in {{clin.n_face_value_right}} tasks and wrong in
  {{clin.n_face_value_wrong}}. The question of the Introduction is answered on this
  grouping, on the scene track (Section 6.4).
- **Offset.** The target residue has an offset in {{clin.n_offset}} tasks, by
  {{clin.offset_min}} to {{clin.offset_max}} residues. This grouping is reported for
  description only.

**Table 2. The two groupings of the {{clin.n}} clinical tasks, crossed.** *Copying the
number* and *offset* as in Box 1.

{{include:generated/table_clinical_groupings.md}}

With a name in UniProt numbering, copying is right exactly when there is no offset. The
groupings differ only for traditional names: in {{clin.n_face_right_offset}} tasks the
structure is numbered from the mature protein as the name is, so the copied number is right
although the residue has an offset. In the one remaining task a traditional name
({{clin.traditional_on_predicted.name}} of haemoglobin beta, which is
{{clin.traditional_on_predicted.hgvs}}) is used on a predicted structure, which has UniProt
numbering: the residue has no offset, but copying the mature-protein number is wrong.
In {{clin.n_offset_pairs_uniprot_name}} sets of two *matched tasks*, the same variant,
named in UniProt numbering, is asked on a structure with an offset and on a predicted
structure without one (SI Section S10.3 lists them, with the rules for tasks that name
several variants).

### 3.4 The same request in two formats

A wrong answer has two possible causes: the model did not know which atoms were meant, or it
knew and could not write them in the format. One format cannot separate the two. MolBench
therefore poses {{corpus.n_twin_pairs}} requests ({{corpus.twin_share_of_mvs:.0%}} of the
scene tasks) on both tracks, with identical wording and the same target atoms (Figure 3).

The formats differ in kind. A MolViewSpec scene [@midlik2025mvs] is declarative: a tree that
states what to load, which atoms to select and how to draw them. A call list is imperative:
each call to the PDBe Mol\* viewer, version 3.3.2 [@pdbemolstar], changes the default view,
so order matters.

The formats also differ in what they demand for a clinical request, and this shapes the
comparison. The call-list viewer can select a residue by UniProt accession and position and
does the mapping itself; a scene must give author or label numbers. On the call-list side of
a clinical pair, a model can thus be right without knowing any residue number of the
structure. Clinical pairs are
therefore read apart from the others (Section 6.3).

![**Figure 3. One request, two formats, the same target atoms.** The scene and the call list are shown in shortened form. Below: for each model, every pair falls into one of four cells by whether each side is right. In the scene, "structure model" is MolViewSpec's name for the deposited coordinates and has nothing to do with a language model. A side is right when at least 2 of its {{plan.samples}} answers are *target-right*: the requested atoms are marked out exactly (a target score of 1, Section 4.2). McNemar's test compares the two shaded cells, in which the model was right in one format only.](generated/fig_twins.svg)

Pairs exist in five categories (Table 1). In {{corpus.twins.need_hide_toggle}} pairs the request asks for something to be shown alone
or for the whole protein in another representation, so the reference call list also
switches off part of the default view, which a scene never needs; these pairs are also
counted apart (SI Section S10.4).

### 3.5 What a request may leave open

One rule says what silence in a request means: **an attribute that the request does not state is free; one that it states must
match.** If the request gives no colour for a ligand, any colour is accepted; if it says
"green", only green is right. Where the open point is which atoms are meant, the task lists
every accepted answer. The rule covers attributes of what was requested, not additions to
the picture such as an unrequested cartoon, which Section 4.2 treats (SI Section S10.5).

### 3.6 Set-aside structures; wording

MolBench tasks have been public since May 2026, so a model released later may have seen
earlier ones. Before generation, {{corpus.heldback.n_structures}} structures that no earlier
release had used were set aside, and the {{corpus.heldback.n_tasks}} tasks on them
({{corpus.heldback.share:.0%}} of the corpus) are reported apart as the *set-aside split*.
The split asks one thing: do models score higher on structures that earlier MolBench tasks
used? A lower score on the split would suggest so. The test is
weak: of the {{corpus.public.n_structures}} other structures only
{{corpus.public.n_structures_used_earlier}} appeared in an earlier release, and nearly all
tasks in both parts are new. Nor is the split a hidden test set: its tasks are public too.

To measure sensitivity to wording, {{corpus.n_requests_paraphrased}} requests
({{corpus.n_tasks_paraphrased}} tasks, because {{corpus.n_paraphrased_pairs}} of them are
pairs) also exist in
a *terse* and an *indirect* phrasing with the same reference; these task files are not
counted in Table 1 (SI Section S10.6).

### 3.7 Checks on the corpus

Four checks involve no model (Figure 1). Every reference and every accepted answer must
select at least one atom, name the residue that the generator intended, and grade as exactly
right against itself. Selections read back from the running viewers agree atom for atom
with the atom tables, and the grader agrees with a control set of {{controls.n:,}} answers
whose verdict is known (Section 4.5). One script validates every task file, and the run
does not start unless every check passes.
