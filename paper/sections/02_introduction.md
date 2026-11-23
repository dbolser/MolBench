## 1. Introduction

Molecular viewers are how structural biologists look at their data, and they are hard to
drive. To show one residue of one chain (one amino acid of one protein molecule in the file), a
user must know how the viewer writes a selection, the chain identifier, and which of several
residue numbering schemes applies. Language models
promise to remove that barrier: the user says what they want, and the model writes the
commands. Several viewers now ship such assistants, or can be operated by one through a
programming interface [@chimeraxmcp; @molstarprism; @navarro2026speak; @sun2024chatmol].

Whether these assistants are right is rarely measured, and a wrong answer is hard to see. One
request, which we follow through this paper and always quote as it is in the task file, shows
why:

> *"{{ex.prompt}}"*

The first sentence of the request states a classification. ClinVar classifies changes at the
level of DNA; in {{variants.records_retrieved:month}} both DNA changes that give {{ex.name_in_prompt}} were classified
as pathogenic (Section 3.2). The benchmark uses the variant only as an address, to ask which
residue the name points to. It never asks whether a variant causes disease (Section 9.2).

The second sentence asks for "the residue it replaces": the tryptophan (W) that the variant
{{ex.name_in_prompt}} turns into an arginine (R). A model that takes the
{{ex.uniprot_position}} of that name as the residue number selects residue
{{ex.uniprot_position}} of the file. That residue is a serine. The model returns a clean
picture of the wrong amino acid, and nothing in the picture says so. The tryptophan is residue
{{ex.auth_number}} of this file.

The two numbers come from two ways of counting. The position {{ex.uniprot_position}} is
counted along the UniProt sequence of human lysozyme (the prefix "p." marks a position in a
protein sequence). That sequence begins with {{ex.removed_what}}, a leading segment that the
cell cuts off after the protein is made. The Protein Data Bank (PDB) entry {{ex.entry}}
numbers the same chain from the first residue of the mature protein, the protein that is left
once that segment has been cut off; older papers accordingly call the variant
{{ex.mature_name}}. The case is not unusual: a survey of the PDB found that 38.6% of 176,507
entries contain proteins that are not numbered as their UniProt sequences are
[@faezov2021pdbrenum].

**What the model is given.** In MolBench the model receives only the request and a guide to
the answer format. It does not see the structure file, it cannot look anything up, and it
does not see the picture that its answer produces. To answer the request above it must
therefore know, from its training, that entry {{ex.entry}} is numbered from the mature
protein. This is the hardest way to ask the question, and it is the way a bare model is used.

**Thesis.** Whether a language model has driven a molecular viewer correctly can be decided
by rule, without a second model as judge, if two conditions hold: each reference answer is
computed from the structure itself, and each answer is graded on what the viewer would draw,
not on how the answer is written.

**Question.** With that instrument we ask one question above the others. When a request gives
a residue number in one numbering and the structure uses another, does the model give the
number that the structure uses, or does it copy the number from the request? We call the first
*mapping* the number and the second *copying* it. Mapping is more than a habit of converting:
some entries are numbered as the request is, and there the copied number is the right one, so
the model must know how each entry is numbered. Section 6.4 is built to answer this.

MolBench is built on this thesis (Figure 1). The reference for the request above is not written
by a person. A script reads the variant from ClinVar [@landrum2018clinvar], maps its UniProt
position [@uniprot2025] to the residues of the entry with the SIFTS mapping [@dana2019sifts],
and confirms that the structure holds a tryptophan there. The grader then resolves an answer
to the atoms it would draw in that structure, with their representation and colour, and
compares this *drawn state* with that of the reference. Two answers that name the same atoms
in different ways receive the same score.

![**Figure 1. From public data to a score.** Boxes 1 to 6 are the steps: frozen public data are turned into tasks by generator scripts; each model is given a guide to the answer format and the request, and answers each task {{plan.samples}} times, independently; the grader resolves the reference and the answer to their drawn state and compares them. Below the steps: the four checks that involve no model (Section 3.7). A *pair* is one request posed on both tracks. *F1*: how much of the drawn state is right, with partial credit. *Task success*: the drawn state is exactly right. *Target score*: the requested atoms are drawn as asked, whatever else was drawn. *Strict* and *valid-only* are two ways to average a score (Section 4.4).](generated/fig_pipeline.svg)

This paper makes four contributions, presented in this order.

1. **A corpus built by script** (Section 3). It has {{corpus.n_tasks}} tasks on
   {{corpus.n_structures}} structures in eight categories of task, which differ in what the
   model must know beyond the request. They include {{clin.n}} clinical-variant requests on
   {{clin.n_proteins}} proteins; in {{clin.n_face_value_wrong}} of them a model that copies
   the number from the variant name selects the wrong residue (Section 3.3.1). Every reference
   records how it was made and is tested against the structure.
2. **A grader on drawn state, tested against a control set** (Section 4). It gives three
   scores with plain definitions, and it is tested on {{controls.n:,}} control answers whose
   verdict is known from how they were made.
3. **A paired design** (Sections 3.4 and 5). In it, {{corpus.n_twin_pairs}} requests are posed in two
   answer formats with the same target atoms, so that an error of content can be told apart
   from an error of format.
4. **A pilot that corrected the benchmark, and a fixed plan for the final run** (Sections 6
   and 7). A pilot run on {{oct.spec.n_models}} models exposed a flaw in our own references
   and changed the design, and one final run will fill tables whose shape is already set.
   ⟦PENDING: final run — one sentence stating the main result⟧

Box 1 defines the terms needed to follow how the benchmark is built (Section 3); Box 2, at the
start of Section 4, defines the terms of grading and of the run.

<div class="box">

**Box 1. Terms and notation: variants, numbering and the corpus.** In this paper *model*
always means a language model. Seven terms carry the results: *track*, *pair*, *copying the
number* (all three below), *drawn state*, *task success*, *target score* and *strict* (Box 2).
The other entries are for reference. Background terms of structural biology (residue, chain,
polymer, entry, predicted structure, ligand, representation, selection) are in SI Section S0.

*Sequences, variants and the viewer.*

| Term | Meaning |
|:---------|:------------------------------|
| UniProt, canonical sequence | UniProt is the reference database of protein sequences. Each protein has an accession, such as {{ex.accession}}, and one sequence that UniProt picks as its reference, the *canonical sequence*. |
| ClinVar | A public archive of human genetic variants. Submitters, mostly clinical laboratories, send their classification of a variant: whether it causes disease. For each *variation record* (accession beginning with VCV; usually one change at the level of DNA, sometimes several changes on one chromosome) ClinVar publishes an aggregate classification of inherited (germline) variants, such as "Pathogenic", and a *review status*. The review status says how far the classification has been reviewed: whether the submitters stated their criteria, whether several submitters agree, and whether an expert panel has reviewed it. It is not a measure of the strength of the evidence. Different DNA changes can give the same amino-acid change, so one amino-acid change can have more than one record. We write ClinVar's terms in lower case from here on. |
| Transcript | A numbered reference copy of the messenger RNA of a gene (accession beginning with NM_). ClinVar states each change on a transcript, in the form {{ex.clinvar_cdna}}: DNA letter {{ex.clinvar_cdna_position}} changes from {{ex.clinvar_cdna_from}} to {{ex.clinvar_cdna_to}}. A gene can have several transcripts, and they can number the protein differently. |
| Missense variant; {{ex.name_in_prompt}} | A change of one amino acid into another. {{ex.name_in_prompt}}: the tryptophan (W) at position {{ex.uniprot_position}} becomes an arginine (R). The same in three-letter form is {{ex.hgvs}}; the prefix "p." marks a position in the protein. A complete description also names the sequence that the position is counted on. In this paper that is the UniProt canonical sequence, here {{ex.accession}}, which is not a reference sequence of the HGVS standard (Section 3.3.1). |
| Signal peptide, mature protein, traditional name | The *mature protein* is what is left after the cell has removed the leading part of a newly made protein. That part can be the first residue alone, the *initiator methionine* (haemoglobin beta); a *signal peptide* (lysozyme: {{ex.offset}} residues); or a signal peptide and a further segment, a *propeptide* (coagulation factor IX: {{clin.f9_removed}} residues). Older literature often numbers residues from the first residue of the mature protein; we call a variant name of this kind a *traditional name* (the genetics literature also says legacy name). It carries no "p.", as in {{ex.mature_name}}. |
| Mol\*, MolViewSpec | Mol\* is an open-source molecular viewer that runs in a web browser. MolViewSpec is a format, written in JSON (JavaScript Object Notation), that describes what Mol\* should load and draw. PDBe Mol\* is the build of Mol\* maintained by the Protein Data Bank in Europe (PDBe). |

*Terms of the corpus.*

| Term | Meaning in this paper |
|:---------|:------------------------------|
| Author numbering | The chain identifiers and residue numbers chosen by the depositors (in the structure file: `auth_asym_id`, `auth_seq_id`). This is what papers and most viewers show. A number can carry an *insertion code*: a letter appended to it (52A) where the depositors placed an extra residue between two numbers. |
| Label numbering | The chain identifiers and residue numbers assigned by the archive (`label_asym_id`, `label_seq_id`). Residues are counted 1, 2, 3 … along the full sequence of the molecule that was studied, including residues that are not seen in the coordinates, so the count has no gaps and no insertion codes. |
| UniProt numbering | The position of a residue in the UniProt canonical sequence, counted from its first residue and so including any signal peptide. The variant names we use are in this numbering unless the request says otherwise (Section 3.3.1). |
| Offset | For one residue, its UniProt number minus its author number ({{ex.uniprot_position}} − {{ex.auth_number}} = {{ex.offset}} in the running example). It can differ from residue to residue within a chain. A residue *has an offset* when the two numbers differ. In every clinical task with an offset the UniProt number is the larger one. |
| Copying the number | Using the number printed in a variant name as the author residue number, without converting it. Copying is *right* in a task if the answer written in this way is exactly right, and *wrong* otherwise (Section 3.3.1). |
| SIFTS | Structure Integration with Function, Taxonomy and Sequences: the public residue-by-residue mapping between PDB entries and UniProt sequences. |
| Structure panel | The fixed set of {{panel.n}} structures (Section 3.1). Tasks are built on {{corpus.n_structures}} of them; one is reserved for the worked example in the prompts. |
| Request | The plain-language instruction given to the model. |
| Task | A request on one track, with its reference answer and, where it has one, its target. A request that is posed on both tracks is two tasks. |
| Answer | What the model returns for one task. Each task is answered {{plan.samples}} times in the main condition. |
| Scene | An answer in MolViewSpec: a description of what to load and how to draw it. A scene groups the atoms it selects into *components*; each component is a named set of atoms that is then drawn in one or more ways. Nothing is on screen unless the scene says so. |
| Call list | An answer as an ordered list of calls to the PDBe Mol\* viewer, written in JSON (Section 3.4). |
| Default view | What the call-list viewer draws as soon as a structure is loaded, before any further call: the whole structure, with the polymer as a cartoon. A scene has no default view; its screen starts empty. |
| Track, format, side | A *track* is one of the two halves of the benchmark. *Scene track*: answers are MolViewSpec scenes. *Call-list track*: answers are call lists. *Format* means the answer language itself (MolViewSpec, or PDBe Mol\* calls). A *side* is one of the two tasks of a pair. |
| Pair | One request posed on both tracks, with the same target atoms. The word is used for nothing else in this paper. |
| Category | One of eight kinds of task (Section 3.3). The categories are not steps on one scale of difficulty. |
| Lookup categories | Name resolution and clinical variant. In these the answer needs one fact that a person would look up in a database: an entry identifier, or a residue number. The model cannot look it up and must recall it. |
| Template | A fixed kind of request within a category; a generator script fills in the structure, the residues, the colours and the wording. |
| Target | The atoms that the request is about. Most tasks store it. For a request that only changes a viewer setting or hides something, the target is everything the reference changes; {{corpus.n_without_target_followup}} follow-up tasks have none (Section 4.2). |
| Accepted answer | One of several drawn states that a task lists as right. An answer is graded against each, and the best result counts. |
| Held-back split | The tasks on {{corpus.heldback.n_structures}} structures that were set aside before generation and kept out of every earlier MolBench release. The tasks are public; the name does not mean a hidden test set (Section 3.6). |

</div>
