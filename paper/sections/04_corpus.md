## 3. Building the benchmark

A task is a request on one track, a reference answer, a record of how the reference was made
and, for most tasks, the atoms that the request is about (the *target*; Section 4.2). No
reference is written by hand. This section follows
the running example from public data to a finished task, and then describes the corpus as a
whole. Box 1 collects its terms.

<div class="box">

**Box 1. Terms and notation: variants, numbering and the corpus.** In this paper *model*
always means a language model. Seven terms carry the results: *track*, *pair*, *copying the
number* (all three below), *drawn state*, *task success*, *target score* and *strict* (Box 2).
The other entries are for reference; further terms of structural biology and of the corpus
are in SI Section S0.

*Sequences, variants and the viewer.*

| Term | Meaning |
|:---------|:------------------------------|
| UniProt, canonical sequence | UniProt is the reference database of protein sequences. Each protein has an accession, such as {{ex.accession}}, and one sequence that UniProt picks as its reference, the *canonical sequence*. |
| ClinVar | A public archive of human genetic variants. Submitters, mostly clinical laboratories, send their classification of a variant: whether it causes disease. For each *variation record* (accession beginning with VCV; usually one change at the level of DNA) ClinVar publishes an aggregate *germline* classification, such as "Pathogenic", and a *review status*. Germline variants are present in every cell of a person, inherited or newly arisen, as opposed to somatic variants that arise in a tumour. The review status says how far the classification has been reviewed (stated criteria, several submitters in agreement, an expert panel); it is not a measure of the strength of the evidence. Different DNA changes can give the same amino-acid change, so one amino-acid change can have more than one record. We write ClinVar's terms in lower case. |
| Transcript | A numbered reference copy of the messenger RNA of a gene (accession beginning with NM_). ClinVar states each change on a transcript, in the form {{ex.clinvar_cdna}}: nucleotide {{ex.clinvar_cdna_position}} of the coding sequence, counted from the A of the start codon ATG, changes from {{ex.clinvar_cdna_from}} to {{ex.clinvar_cdna_to}}. A gene can have several transcripts, and they can number the protein differently. |
| Missense variant; {{ex.name_in_prompt}} | A change of one amino acid into another. {{ex.name_in_prompt}}: the tryptophan (W) at position {{ex.uniprot_position}} becomes an arginine (R). The same in three-letter form is {{ex.hgvs}}. The prefix "p." marks a description of a change in the protein, as opposed to "c." for the coding DNA; it does not say which sequence the position is counted on. In this paper that is the UniProt canonical sequence, here {{ex.accession}}, which is not a reference sequence in the sense of the HGVS nomenclature, the standard of the Human Genome Variation Society for naming variants (Section 3.3.1). |
| Signal peptide, mature protein, traditional name | The *mature protein* is what is left after the cell has removed the leading part of a newly made protein. That part can be the first residue alone, the *initiator methionine* (haemoglobin beta); a *signal peptide* (lysozyme: {{ex.offset}} residues); or a signal peptide and a further segment, a *propeptide* (coagulation factor IX: {{clin.f9_removed}} residues). Older literature often numbers residues from the first residue of the mature protein; we call a variant name of this kind a *traditional name* (the genetics literature also says legacy name). It carries no "p.", as in {{ex.mature_name}}. |
| Mol\*, MolViewSpec | Mol\* is an open-source molecular viewer that runs in a web browser. MolViewSpec is a format, written in JSON (JavaScript Object Notation), that describes what Mol\* should load and draw. PDBe Mol\* is the build of Mol\* maintained by the Protein Data Bank in Europe (PDBe). |
| Polymer, ligand | The *polymer* is the protein, DNA or RNA chains of a structure. A *ligand* is a small molecule bound to them. |
| Representation | A way of drawing atoms: *cartoon* (a ribbon that traces the whole polymer chain, the usual background of a picture), *ball-and-stick*, *spacefill* (every atom as a full-size sphere), *surface*. |

*Terms of the corpus.*

| Term | Meaning in this paper |
|:---------|:------------------------------|
| Author numbering | The chain identifiers and residue numbers chosen by the depositors (in the structure file: `auth_asym_id`, `auth_seq_id`). This is what papers and most viewers show. A number can carry an *insertion code*: a letter appended to it (52A) where the depositors placed an extra residue between two numbers. |
| Label numbering | The chain identifiers and residue numbers assigned by the archive (`label_asym_id`, `label_seq_id`). Residues are counted 1, 2, 3 … along the full sequence of the molecule that was studied, including residues that are not seen in the coordinates, so the count has no gaps and no insertion codes. |
| UniProt numbering | The position of a residue in the UniProt canonical sequence, counted from its first residue and so including any signal peptide. The variant names we use are in this numbering unless the request says otherwise (Section 3.3.1). |
| Offset | For one residue, its UniProt number minus its author number ({{ex.uniprot_position}} − {{ex.auth_number}} = {{ex.offset}} in the running example). It can differ from residue to residue within a chain. A residue *has an offset* when the two numbers differ. In every clinical task with an offset the UniProt number is the larger one. |
| Copying the number | Using the number printed in a variant name as the author residue number, without converting it. Copying is *right* in a task if the answer written in this way is exactly right, and *wrong* otherwise. The property is defined on author numbering and is used to group results of the scene track only (Section 3.3.1). |
| Request, task, answer | The *request* is the plain-language instruction given to the model. A *task* is a request on one track, with its reference answer and, where it has one, its target; a request that is posed on both tracks is two tasks. An *answer* is what the model returns for one task. Each task is answered {{plan.samples}} times in the main condition. |
| Target | The atoms that the request is about. Most tasks store it. For a request that only changes a viewer setting or hides something, the target is everything the reference changes; {{corpus.n_without_target_followup}} follow-up tasks have none (Section 4.2). |
| Scene | An answer in MolViewSpec: a description of what to load and how to draw it. A scene groups the atoms it selects into *components*; each component is a named set of atoms that is then drawn in one or more ways. Nothing is on screen unless the scene says so. |
| Call list | An answer as an ordered list of calls to the PDBe Mol\* viewer, written in JSON (Section 3.4). |
| Default view | What the call-list viewer draws as soon as a structure is loaded, before any further call: the whole structure, with the polymer as a cartoon. A scene has no default view; its screen starts empty. |
| Track, format | A *track* is one of the two halves of the benchmark. *Scene track*: answers are MolViewSpec scenes. *Call-list track*: answers are call lists. *Format* means the answer language itself (MolViewSpec, or PDBe Mol\* calls). |
| Pair, side | A *pair* is one request posed on both tracks, with the same target atoms. A *side* is one of the two tasks of a pair. Both words are used for nothing else in this paper. |

</div>

### 3.1 Frozen public data

**Structures.** All tasks use a fixed *structure panel* of {{panel.n}} structures, namely
{{panel.n_pdb}} PDB entries [@wwpdb2019] and {{panel.n_alphafold}} predicted structures from
the AlphaFold Protein Structure Database [@varadi2024afdb]. One PDB entry,
{{prompt.worked_example_entry}}, is reserved for the worked example of both system prompts,
so tasks use {{corpus.n_structures}}. The panel was chosen for
coverage, not at random: proteins alone, with bound small molecules or metal ions, with DNA or
RNA, with attached sugars, and membrane proteins. Of the PDB entries, {{panel.n_xray}} were solved by X-ray
crystallography, {{panel.n_cryoem}} by cryo-electron microscopy and {{panel.n_nmr}} by nuclear
magnetic resonance. The {{panel.n_alphafold}} predicted structures are of
{{panel.alphafold_proteins}}; each of these proteins also has an experimental structure in the
panel, and a predicted structure uses UniProt numbering. In {{panel.n_offset}} of the
{{panel.n}} structures at least one residue has an offset: its author number differs from its
UniProt number. Every
feature that we claim for an entry is verified in its file by the build script, or the build
fails. The Supporting Information (SI, Section S3) lists the panel, its features and its
selection rule.

**Disease proteins and variants.** The panel includes structures of
{{panel.n_disease_proteins}} human proteins in which germline missense variants cause
Mendelian disease (missense: one amino acid is replaced by another; germline: the variant is
in every cell of a person). We chose the proteins by hand, as familiar
examples that have experimental structures. For each protein, one PDB entry was then chosen
by a scripted rule that did not look at how the entry is numbered (SI Section S3). A protein
can still have tasks on more than one structure: on its chosen entry, on its predicted
structure where the panel has one, and on another panel entry that also contains it ({{clin.n_structures_two_proteins:word}}
haemoglobin entries hold both the alpha and the beta chain). In all,
{{clin.n_proteins_several_structures}} proteins have tasks on more than one structure.

**The pool of variants.** UniProt lists {{variants.n_candidates:,}} missense variants of
these proteins as pathogenic or likely pathogenic. We keep a variant only if a ClinVar record
that UniProt cross-references confirms it: the record gives the same amino-acid change a
pathogenic or likely pathogenic aggregate germline classification
({{variants.n_removed_by_clinvar}} candidates have no such record and were removed), and it
is a record of the gene named in the request, describes that change alone, and states the
criteria of the classification (a further {{variants.n_second_pass_removed}} were removed).
The remaining {{variants.n_usable:,}} variants form the pool. We did not search ClinVar beyond
UniProt's cross-references. SI Table S4 gives the filter step by step, and SI Section S3.2
the dates on which the data were read.

Two exceptions were made by hand (SI Section S3.2). One well-known lysozyme variant,
p.Ile74Thr, is outside the pool because its ClinVar record states no criteria. We use it all
the same, in {{clin.n_tasks_kept_by_name:word}} task per track; its request says, as the
record does, that the variant is classified as {{clin.kept_by_name.classification}} in
ClinVar. One *APOE* variant inside the pool is never asked about, because it is better known
for a reported protective effect and a request that calls it pathogenic would mislead.

**From the pool to the clinical tasks.** A clinical task asks about one variant, or a few, on
a panel structure of its protein. The generator picks the variant by seeded random choice
among the pool variants whose residue is observed in the structure with the amino acid of the
reference sequence. For {{clin.n_featured_proteins}} proteins a well-known variant, named by
hand before generation, is tried first (for example the sickle-cell variant of haemoglobin
beta, p.Glu7Val; SI Section S3.2 has the list). The result is
{{clin.n}} tasks per track on {{clin.n_proteins}} proteins and {{clin.n_structures}}
structures ({{clin.n_pdb_structures}} PDB entries and the {{panel.n_alphafold}} predicted
structures), with at most {{clin.max_tasks_per_structure}} tasks per track on one structure.
The other {{panel.n_disease_proteins_without_task:word}} proteins have no task, because no
variant of the pool is observed in their panel structure (SI Section S3.2).

**Atom tables and residue mapping.** For each structure we freeze two tables. The *atom table*
is built from the entry's file in the PDB archive, in the archive's mmCIF format (for a
predicted structure, the file of the AlphaFold Protein Structure Database). It lists every
atom record of the first coordinate set (the first "model" in PDB terms; we avoid that word
because *model* here means a language model), with its chain and residue in both author and label
numbering, and it keeps hydrogen atoms and alternate positions of an atom where the file has
them: a selection of a residue takes all of its atom records, as the viewer does. The
*mapping table* holds the SIFTS correspondence between each observed residue and its UniProt
position. Generators and graders read only these tables, and nothing is fetched while a task
is built from the tables, graded or loaded. The atom table is compared with what the viewer
itself selects in the same file (Section 3.7); SI Section S3.1 gives the details.

### 3.2 From data to a task: the running example

The clinical generator produced the running example in six steps.

1. **Variant.** From the pool it picks the *{{ex.gene}}* variant {{ex.name_in_prompt}}
   ({{ex.hgvs}}; UniProt {{ex.accession}}). Through UniProt's cross-references we found
   {{ex.n_clinvar_records}} ClinVar records of this protein change, one for each of the two
   single-nucleotide changes that turn the codon of this tryptophan into a codon of arginine
   ({{ex.clinvar_records}}). As read on {{variants.records_retrieved:date}}, both
   are classified as {{ex.clinvar_classification}}, with the review status
   "{{ex.clinvar_review_status}}": one laboratory submitted the classification and stated its
   criteria, and no second submitter or expert panel has confirmed it. The field of the
   record that names the condition reads "{{ex.clinvar_conditions}}".
2. **Structure.** The panel entry for {{ex.accession}} is {{ex.entry}}, human lysozyme.
3. **Mapping.** The mapping table says that UniProt positions
   {{ex.map_uniprot_first}}–{{ex.map_uniprot_last}} are author residues
   {{ex.map_auth_first}}–{{ex.map_auth_last}} of author chain {{ex.auth_chain}}: an offset of
   {{ex.offset}}, the length of the signal peptide. Position {{ex.uniprot_position}} is
   therefore author residue {{ex.auth_number}} (label chain {{ex.label_chain}}, label residue
   {{ex.label_number}}).
4. **Identity check.** The atom table must hold the amino acid of the reference sequence at
   that residue. It does: {{ex.wild_type}}{{ex.auth_number}}, {{ex.n_target_atoms}} atom
   records ({{ex.n_target_heavy_atoms}} non-hydrogen atoms and {{ex.n_target_hydrogens}}
   hydrogens; this entry, at {{ex.resolution}} Å resolution, includes hydrogens). Had
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
cartoon (the *default view*, Box 1), and a colouring call also recolours the residue's own segment of that
cartoon unless an option switches this off. The request says nothing about the cartoon, so the
call-list task accepts both results: the segment unchanged, or the segment recoloured (SI
Section S1).

The reference contains only what the request states: one residue, one representation, one
colour. It has no cartoon of the protein behind the residue, because the request does not ask
for one. Section 6.6 shows why this rule exists. SI Section S1 gives both tasks in full.

### 3.3 Eight categories of task

Tasks are grouped into eight *categories* (Figure 2, Table 1). Four differ in what the model
must know beyond the request: nothing (translation), what the entry contains
(structure-grounded), which entry holds a protein (name resolution), or which residue number
a variant has in the entry (clinical variant). The other four differ in the form of the task:
single atoms and drawings between them (interactions), an edit to a given state (follow-up
turn), a request with several right answers, and settings that only one format has (viewer
settings). The categories are kinds of task, not steps on one scale of difficulty. Each
category has several *templates*: a template fixes what is asked, and a seeded generator fills
in the structure, the residues, the colours and the wording. The corpus has
{{corpus.n_templates}} templates. No template supplies more than
{{corpus.max_template_share_other:.0%}} of a category's tasks, except in name resolution (there
are only five ways to name a protein) and in the small call-list category of requests with
several right answers. SI Section S2 lists every template with an example.

![**Figure 2. The eight categories of task, with one request each.** Counts are tasks on the scene track / the call-list track; a dash means that the category has no task on that track (Table 1 gives the reasons). Requests are quoted from the corpus; a long one is cut short. Two words in them are file terms: a *het group* is a molecule in the entry that is not part of a polymer chain, such as a ligand, named by an identifier of up to three characters; *C-alpha* is the central carbon atom of an amino acid. Framed in blue: the two *lookup categories*, name resolution and clinical variant, in which the answer needs one fact that a person would look up in a database and that the model must recall.](generated/fig_tiers.svg)

- **Translation.** Everything needed is in the request: the entry, the chains, the residue
  numbers, the colours. The model only has to write it in the format.
- **Structure-grounded.** The request names a feature, such as the ligand, the disulfide bonds
  (links between two cysteine residues) or the residues that hold a metal ion. The model does
  not see the file. It must either use a generic selector of the format where one fits (for
  example "ligand") or recall what the entry contains, such as the identifier of the ligand
  or the numbers of the residues. The references are computed from the entry's own records.
- **Interactions.** As in translation, the request states everything, so nothing more must be
  known about the structure. What differs is what must be written: single atoms are selected,
  not whole residues, and something is drawn between or around them, such as a hydrogen bond
  as a dashed line labelled with its length, with the camera centred on it.
- **Name resolution.** The request names a protein, not an entry ("a structure of human p53
  bound to DNA"). Any entry on a frozen list of the PDB entries of that protein is accepted
  (SI Section S4.4 gives the rule and the date of the list). An answer on a panel entry is
  graded on drawn state. An answer on an accepted entry outside the panel is compared with
  the reference as written, because we hold no atom table for it; this is a limit (Sections
  4.1 and 9.3). The two kinds of answer are reported in separate rows (Section 6.2).
- **Clinical variant.** As in the running example: the request names a variant, and the model
  must find its residue in the structure, where its number often differs from the one in the
  name. Section 3.3.1 describes this category.
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
leaves out is one fact that a person would look up in a database: which entry holds the
protein, or which residue number the variant has in the entry. The model cannot look it up and
must recall it. Only these two categories have a grounding pack, in which the lookup has been
done for the model (Section 5.2).

**Table 1. The corpus.** Tasks per category and track, written as total (public + held back;
Section 3.6). *Pairs*: requests posed on both tracks with the same target atoms. A dash means
that the category has no task on that track. For interactions (on the call-list track) and
viewer settings (on the scene track) the format cannot express what is asked. Name resolution
could be asked on the call-list track but is not: the call-list grader has no atom table for
an entry outside the panel (Section 3.4).

{{include:generated/table_corpus.md}}

The {{corpus.n_tasks}} tasks ({{corpus.mvs.n}} on the scene track, {{corpus.api.n}} on the
call-list track) use {{corpus.n_structures}} of the {{panel.n}} panel structures. No structure
appears in more than {{corpus.max_tasks_per_structure_tier_track}} tasks of one category and
track. The call-list track has more translation tasks than the scene track because its format
has many single-purpose calls and selectors. Of its {{corpus.api.translation.n}} translation
tasks, {{corpus.api.translation.n_call_only}} (from
{{corpus.api.translation.n_call_only_templates}} templates) exercise calls that have no
counterpart in a scene; the other {{corpus.twins.translation}} are pairs.

#### 3.3.1 The clinical category

There are {{clin.n}} clinical tasks per track, on {{clin.n_proteins}} proteins and
{{clin.n_structures}} structures. Of these, {{clin.n_one_variant}} name one variant; the other
{{clin.n_multi}} name several, up to {{clin.max_variants_per_task}}. In all, the requests
name {{clin.n_variants}} distinct variants; a variant that is asked about on two structures
(matched tasks, below) is counted once. No target residue has an insertion code.

*How variants are named.* The requests use three forms of name. Three-letter names
({{ex.hgvs}}) and one-letter names ({{ex.name_in_prompt}}) carry the prefix "p.". In this
corpus a name with "p." is always in UniProt numbering; the prefix itself does not say so.
*Traditional names* ({{ex.mature_name}}) carry no prefix and are counted along the mature
protein, as in older literature. The first two forms follow the protein-level style of the
HGVS nomenclature, the standard of the Human Genome Variation Society for naming variants
[@denDunnen2016hgvs; @hart2024hgvs], but they are not complete HGVS descriptions. A complete
description puts a reference sequence with its version number before the "p."; for a protein
change this is a protein accession of RefSeq or Ensembl (beginning with NP_ or ENSP). A
UniProt accession, which {{clin.n_accession_in_prompt}} requests state, is not such a
reference sequence. HGVS also prefers the three-letter form, and it puts parentheses around a
protein change that is predicted from the DNA change and was not observed in the protein.

ClinVar itself states each change on a *transcript*, a numbered reference copy of the gene's
messenger RNA. For the running example the name is {{ex.clinvar_first_title}}: nucleotide
{{ex.clinvar_cdna_position}} of the coding sequence of transcript {{ex.clinvar_transcript}},
counted from the A of the start codon ATG, changes from {{ex.clinvar_cdna_from}} to
{{ex.clinvar_cdna_to}}, which is predicted to change the protein as given in parentheses.
ClinVar's names carry the protein change in parentheses for the reason just given. A gene can
have several transcripts, and they can number the protein differently, so a ClinVar record
lists the protein change once for each transcript. We accept a record if any one of these
names equals our amino-acid change and position. We did not check which transcript that name
is counted on; we take its position to be that of the UniProt canonical sequence (Section
9.2).

The request asks for the residue in one of three wordings: "the residue it replaces", "the
residue replaced by" the variant, or "the wild-type residue at the position of" the variant.
All three mean the amino acid of the reference sequence at that position; the third uses
"wild-type", the usual word in structural biology, where clinical genetics would say
"reference".

*Traditional names.* A traditional name is used in {{clin.n_mature_name}} requests (for
example transthyretin V30M, which is p.Val50Met). Each of these requests says so, and says
what the traditional numbering leaves out. One of them in full:

> *"{{clin.mature_example.prompt}}"*

In UniProt numbering this variant is {{clin.mature_example.hgvs}}. Entry
{{clin.mature_example.entry}} is numbered from the mature protein as well, so here the
printed {{clin.mature_example.number}} is the author residue number, and copying it is right.
Of the
{{clin.n_mature_name}} traditional names, {{clin.n_traditional_init_met}} differ from the
UniProt number by the initiator methionine alone (by 1), {{clin.n_traditional_signal}} by a
signal peptide, and {{clin.n_traditional_signal_propeptide}} by a signal peptide and a
propeptide.

*Two groupings.* Each clinical task has two yes-or-no properties that matter for the results.
They are not the same property (Table 2a).

- **Copying the number** (the primary grouping). If an answer uses the number printed in the
  variant name as the author residue number, is it right? Copying is right in
  {{clin.n_face_value_right}} tasks and wrong in {{clin.n_face_value_wrong}}. The property is
  defined on author numbering, and it describes what copying does on the scene track, where
  the model must give an author or a label number. On the call-list track the printed number
  can also be passed unchanged to the viewer's UniProt selector (Section 3.4), which is right
  for every name in UniProt numbering, so results are grouped by this property on the scene
  track only (Section 6.4).
- **Offset** (a descriptive grouping). Does the author number of the target residue differ
  from its UniProt number? An offset is present in {{clin.n_offset}} tasks
  ({{clin.offset_share:.0%}}) and absent in {{clin.n_no_offset}}. Where there is one, the
  UniProt number is always the larger, by {{clin.offset_min}} to {{clin.offset_max}}
  residues.

A task with several target residues is assigned by rule. Copying counts as right only if the
answer with every number copied is exactly right, that is, if copying is right for every named
variant. The task has an offset if any of its target residues has one. In a task that asks for
a helix or strand, both properties are those of the variant's residue, not of the whole helix
or strand. As it turns out, all {{clin.n_multi}} tasks with several variants and all
{{clin.n_sse}} helix or strand tasks have an offset, and copying is wrong in all of them.

**Table 2a. The two groupings of the {{clin.n}} clinical tasks, crossed.** *Copying the number*:
an answer that uses the number printed in the variant name as the author residue number is
right, or wrong. *Offset*: the author number of the target residue differs from its UniProt
number, or does not. A task with several target residues has an offset if any of them has
one, and copying is right in it only if it is right for all of them.

{{include:generated/table_clinical_groupings.md}}

With a name in UniProt numbering, copying is right exactly when there is no offset. The two
groupings differ only for the {{clin.n_mature_name}} traditional names. In
{{clin.n_face_right_offset}} of them the entry is numbered in the same traditional way, so the
number in the name is the author number although the UniProt number is not. The one
remaining traditional name ({{clin.traditional_on_predicted.name}} of haemoglobin beta, which
is {{clin.traditional_on_predicted.hgvs}}) is asked on a predicted structure, which
uses UniProt numbering. There, copying the traditional number selects the wrong residue
although the target has no offset (the single task in the top-right cell of Table 2a).

*Further properties.* Table 2b lists five further properties of the clinical tasks. One needs
a remark. Where a request states no UniProt accession and names the variant with "p.",
neither the request nor the system prompt says which sequence the position is counted on. The
model must take it to be the full-length protein. A reader of a bare name with "p." would
normally take it to be the protein of the gene's default transcript; we assume, and did not
check, that this protein is numbered as the UniProt canonical sequence is (Section 9.2).

**Table 2b. Further properties of the {{clin.n}} clinical tasks.** *Tasks*: number of tasks
per track with the property. Indented rows divide the row above them. *Traditional name*: a
name counted along the mature protein, without "p."; the request then says how the name is
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
| The helix or strand that contains the residue is also asked for (the two common local shapes of a protein chain, as recorded in the entry) | {{clin.n_sse}} | The model must also know where the entry records that helix or strand to begin and end; these tasks are reported apart. |

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

### 3.4 The same request in two formats

A wrong answer has two possible causes: the model did not know which atoms were meant, or it
knew and could not write them in the format. One format cannot separate the two. MolBench
therefore poses {{corpus.n_twin_pairs}} requests ({{corpus.twin_share_of_mvs:.0%}} of the scene
tasks) on both tracks, with identical wording and the same target atoms (Figure 3).

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
model must produce author or label numbers. The running example's call-list reference uses the
UniProt selector; its scene reference uses author residue {{ex.auth_number}}. Any selection
that the format allows is accepted if it resolves to the right atoms: author or label
numbering on the scene track, and those two or the UniProt selector on the call-list track. On
the call-list side of a clinical pair, a model can thus be right without knowing any residue
number of the entry. When the request states the accession and the name is in UniProt
numbering ({{clin.n_accession_uniprot}} of the {{clin.n}} clinical requests), the model only
has to pass the accession and the position on to the right call. When the name is in UniProt
numbering and no accession is stated ({{clin.n_no_accession_uniprot}}), it must also know the
accession.

The {{clin.n_mature_name}} requests with a traditional name are a separate case. Their printed
number is not the UniProt position, so the UniProt selector gives the wrong residue if the
number is passed on as printed; the call-list reference uses the selector with the converted
position. In {{clin.n_face_right_offset}} of the {{clin.n_mature_name}} the printed number is
the entry's author number, so on either track an answer that selects by author number with
the printed number is right. In the remaining one, on a predicted structure, the model must
convert the number on either track. The format guide of the call-list track documents the UniProt selector, and the
guide of the scene track documents selection by author and by label numbering; neither says
which numbering a given entry uses (Section 5.2).

The grader resolves the UniProt selector through the frozen mapping table. The viewer reads
the same SIFTS mapping from the structure file that PDBe distributes. We did not replay
UniProt selections on PDB entries in the viewer (Section 3.7), so for these entries the
agreement between grader and viewer rests on both using SIFTS.

![**Figure 3. One request, two formats, the same target atoms.** The scene and the call list are shown in shortened form. Below: for each model, every pair falls into one of four cells by whether each side is right. The primary comparison counts a side as right when at least 2 of its {{plan.samples}} answers are *target-right*, that is, have a target score of exactly 1 (the requested atoms drawn as asked, whatever else was drawn). It uses the {{corpus.twins.n_with_target}} pairs that have a target score; it is repeated with task success in place of the target score, on all {{corpus.n_twin_pairs}} pairs (Section 5.4). McNemar's test compares the two shaded cells, in which the model was right in one format only.](generated/fig_twins.svg)

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

### 3.5 What a request may leave open

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

### 3.6 Public and held-back tasks; wording

MolBench tasks have been public since May 2026, so a model released later may have seen
earlier tasks. Two measures address this.

*Held-back split.* Before generation, {{corpus.heldback.n_structures}} structures were set
aside: no earlier MolBench release used them, and no task of the public split uses them.
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
share a protein with a public structure. What would be informative is a clearly lower score
on the held-back structures: it would suggest that scores on the public structures profit
from earlier tasks on them or from their being better known. A difference near zero would not
show the opposite. We report the difference between the splits with an interval and do not
test it, because the split is small (Section 9.4).

*Wording.* To measure sensitivity to wording, {{corpus.n_requests_paraphrased}} requests of
the public split have, beside their original (*full*) wording, two further phrasings each, a
*terse* one and an *indirect* one, with the same reference. For example, the request "{{corpus.paraphrase_example.full}}" also exists in
a terse form ("{{corpus.paraphrase_example.terse}}") and in an indirect form
("{{corpus.paraphrase_example.indirect}}"). Of the
{{corpus.n_requests_paraphrased}} requests, {{corpus.n_paraphrased_pairs}} are pairs, so they are
{{corpus.n_tasks_paraphrased}} tasks, and two further phrasings of each give
{{corpus.n_paraphrase_files}} additional task files. These are not counted in Table 1.

### 3.7 Checks on the corpus

Four checks involve no model (Figure 1).

- **Reference against structure.** Every reference must select at least one atom, must name the
  residue that the generator intended, and must grade as exactly right against itself. Every
  accepted answer must do the same.
- **Atom tables against the viewer.** Selections were read back from the running viewers and
  compared atom for atom with the atom tables: for {{controls.viewer.mvs.checked}} scene
  controls in Mol\* 5.9.0, and for a sample of {{controls.viewer.api.sample}} call-list
  controls in PDBe Mol\* 3.3.2. All agreed. The default view after a load with no further call
  was compared in the same way for {{controls.viewer.api.bare_loads}} of the {{panel.n_pdb}}
  PDB entries of the panel. Section 4.5 gives the details and lists what was not checked.
- **Grader against a control set.** The grader is run on {{controls.n:,}} answers whose
  verdict is known (Section 4.5).
- **Format rules.** One script validates every task file against the written task format, and
  the run does not start unless every check passes.
