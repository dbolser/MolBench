## 1. Introduction

Molecular viewers are how structural biologists look at their data, and they are hard to
drive. The data are *structures*: the three-dimensional atom coordinates of molecules. Each
structure deposited in the Protein Data Bank (PDB) is an *entry* with a four-character
identifier, such as {{ex.entry}}. To show one residue of one chain (one amino acid of one protein molecule in the file), a
user must know how the viewer writes a selection, the chain identifier, and which of several
residue numbering schemes applies. Language models
promise to remove that barrier: the user says what they want, and the model writes the
commands. Several viewers now ship such assistants, or can be operated by one through a
programming interface [@chimeraxmcp; @molstarprism; @navarro2026speak; @sun2024chatmol].

Whether these assistants are right is rarely measured, and a wrong answer is hard to see. One
request, which we follow through this paper and always quote as it is in the task file, shows
why:

> *"{{ex.prompt}}"*

The request asks for "the residue it replaces": the tryptophan (W) that the variant
{{ex.name_in_prompt}} turns into an arginine (R). A model that takes the
{{ex.uniprot_position}} of that name as the residue number selects residue
{{ex.uniprot_position}} of the file. That residue is a serine. The model returns a clean
picture of the wrong amino acid, and nothing in the picture says so. The tryptophan is residue
{{ex.auth_number}} of this file.

The two numbers come from two ways of counting. The position {{ex.uniprot_position}} is
counted along the sequence of human lysozyme in UniProt, the reference database of protein
sequences (the prefix "p." marks a description of a change in a protein). That sequence
begins with {{ex.removed_what}}, a leading segment that the cell cuts off after the protein
is made. Entry {{ex.entry}} numbers the same chain from the first residue of the mature protein, the protein that is left
once that segment has been cut off; older papers accordingly call the variant
{{ex.mature_name}}. The case is not unusual: a survey of the PDB found that 38.6% of 176,507
entries contain proteins that are not numbered as their UniProt sequences are
[@faezov2021pdbrenum].

The request also states a classification. It comes from ClinVar, a public archive of human
genetic variants and their clinical classification. The benchmark uses the variant only as an
address: which residue does the name point to? It never asks whether a variant causes disease
(Section 9.2; Section 3.2 gives the ClinVar record of this variant).

**What the model is given.** In MolBench the model receives only the request and a guide to
the answer format. It does not see the structure file, it cannot look anything up, and it
does not see the picture that its answer produces. To answer the request above it must
therefore know, from its training, that entry {{ex.entry}} is numbered from the mature
protein. This is the hardest way to ask the question, and it is the way a model is used when
it has no tools (a *bare* model).

**Thesis.** Whether a language model has driven a molecular viewer correctly can be decided
by rule, without a second model as judge, if two conditions hold: each reference answer is
computed from the structure itself, and each answer is graded on what the viewer would draw,
not on how the answer is written.

MolBench is a benchmark built on this thesis (Figure 1). The reference for the request above
is not written by a person. A script reads the variant from ClinVar [@landrum2018clinvar],
maps its UniProt position [@uniprot2025] to the residues of the entry with the SIFTS mapping
[@dana2019sifts], a public table that gives, for each residue of a PDB entry, its position in
the UniProt sequence, and confirms that the structure holds a tryptophan there. The grader then
resolves an answer to the atoms it would draw in that structure, with their *representation*
and colour, and compares this *drawn state* with that of the reference. A representation is a
way of drawing atoms: the request above asks for spacefill spheres (every atom as a full-size
sphere), and the usual background of a protein picture is a *cartoon*, a ribbon that traces
the whole chain. Two answers that name the same atoms in different ways receive the same
score.

**Question.** With this benchmark we ask one question above the others. When a request gives
a residue number in one numbering and the structure uses another, does the model give the
number that the structure uses, or does it copy the number from the request? We call the first
*mapping* the number and the second *copying* it. Mapping is more than a habit of converting:
some structures are numbered as the request is, and there the copied number is the right
one, so the model must know how each structure is numbered. Section 6.4 sets out the table that will
answer this.

![**Figure 1. From public data to a score.** Steps 1 to 6 are numbered, in two rows: frozen public data are turned into tasks by generator scripts; each model is given a guide to the answer format and the request, and answers each task {{plan.samples:word}} times, independently; the grader resolves the reference and the answer to their drawn state and compares them. Below the steps: the four checks that involve no model (Section 3.7). A *pair* is one request posed on both tracks. *Set-aside structures*: {{corpus.heldback.n_structures}} structures that no earlier release of the benchmark used; their tasks are public too (Section 3.6). *F1*: how much of the drawn state is right, with partial credit. *Task success*: the drawn state is exactly right. *Target score*: how far the requested style is on the requested atoms and on no others (0 to 1); unrequested background, such as a cartoon of the protein, is ignored. *Strict* and *valid-only* are two ways to average a score (Section 4.4).](generated/fig_pipeline.svg)

This paper makes four contributions, presented in this order.

1. **A corpus built by script** (Section 3). It has {{corpus.n_tasks}} tasks on
   {{corpus.n_structures}} structures in eight categories of task: four differ in what the
   model must know beyond the request, and four in the form of the task (Section 3.3). They
   include {{clin.n}} clinical-variant requests on
   {{clin.n_proteins}} proteins; in {{clin.n_face_value_wrong}} of them a model that copies
   the number from the variant name selects the wrong residue (Section 3.3.1). Every reference
   records how it was made and is tested against the structure.
2. **A grader on drawn state, tested against a control set** (Section 4). It gives three
   scores with plain definitions, and it is tested on {{controls.n:,}} control answers whose
   verdict is known from how they were made.
3. **A paired design** (Sections 3.4 and 5). The benchmark has two halves, which we call
   *tracks*. On the *scene track* an answer is a MolViewSpec scene, a description of what the
   Mol\* viewer should load and draw. On the *call-list track* it is an ordered list of calls
   to the PDBe Mol\* viewer. {{corpus.n_twin_pairs}} requests are posed on both tracks with the
   same target atoms, so that an error of content can be told apart from an error of format.
4. **A pilot that corrected the benchmark, and a fixed plan for the final run** (Sections 6
   and 7). A pilot run on {{oct.spec.n_models}} models exposed a flaw in our own references
   and changed the design, and one final run will fill tables whose shape is already set.
   ⟦PENDING: final run — one sentence stating the main result⟧

Terms are defined where they are first used and collected in two boxes: Box 1, at the start
of Section 3, has the terms of variants, numbering and the corpus, and Box 2, at the start of
Section 4, those of grading and of the run.
