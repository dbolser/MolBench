## 1. Introduction

Molecular viewers are how structural biologists look at their data, and they are hard to
drive. The data are *structures*: the three-dimensional atom coordinates of molecules. To
show one residue (one amino acid) of one protein chain, a user must know how the viewer
writes a selection, how the chain is named, and which of several residue numberings
applies. Language models promise to remove that barrier: the user says what they want, and
the model writes the commands. Several viewers now ship such assistants or can be operated
by one [@chimeraxmcp; @molstarprism; @navarro2026speak; @sun2024chatmol].

Whether these assistants are right is rarely measured, and a wrong answer is hard to see.
One request, which we follow through this paper, shows why:

> *"{{ex.prompt}}"*

Here {{ex.entry}} is an *entry* of the Protein Data Bank (PDB), one deposited structure, and
{{ex.name_in_prompt}} is a variant that turns a tryptophan (W) into an arginine (R). The
request asks for that tryptophan. A model that takes the {{ex.uniprot_position}} of the name
as the residue number selects residue {{ex.uniprot_position}} of the file, which is a serine.
It returns a clean picture of the wrong amino acid, and nothing in the picture says so. The
tryptophan is residue {{ex.auth_number}} of this file.

The two numbers come from two ways of counting. Position {{ex.uniprot_position}} is counted
along the sequence of human lysozyme in UniProt, the reference database of protein
sequences. That sequence begins with {{ex.removed_what}}, which the cell cuts off; the file
numbers the chain from the first residue of the protein that is left. The case is not
unusual: in a survey of the PDB, 38.6% of 176,507 entries contained proteins that are not
numbered as their UniProt sequences are [@faezov2021pdbrenum].

**What the model is given.** In MolBench the model receives only the request and a guide to
the answer format. It does not see the structure file, it cannot look anything up, and it
does not see the picture that its answer produces. To answer the request above it must know
from its training how entry {{ex.entry}} is numbered. The classification in the request
comes from ClinVar, a public archive of human genetic variants; the benchmark uses a variant
only as an address for a residue and never asks whether it causes disease.

**Thesis.** Whether a language model has driven a molecular viewer correctly can be decided
by rule, without a second model as judge, if two conditions hold: each reference answer is
computed from the structure itself, and each answer is graded on what the viewer would draw,
not on how the answer is written.

MolBench is built on this thesis (Figure 1). The reference for the request above is not
written by a person. A script reads the variant from ClinVar [@landrum2018clinvar], maps its
UniProt position [@uniprot2025] to the residue of the entry with SIFTS [@dana2019sifts], a
public table that gives the UniProt position of each residue of a PDB entry, and confirms
that the structure holds a tryptophan there. The grader then resolves an answer to the atoms
it would draw, with their *representation* (the way atoms are drawn, here spacefill spheres)
and colour, and compares this *drawn state* with that of the reference. Two answers that
name the same atoms in different ways receive the same score.

**Question.** When a request gives a residue number in one numbering and the structure uses
another, does the model give the number that the structure uses, or does it copy the number
from the request? We call the first *mapping* the number and the second *copying* it.
Mapping is more than a habit of converting: some structures are numbered as the request is,
and there the copied number is right, so the model must know how each structure is numbered.

![**Figure 1. From public data to a score.** Frozen public data are turned into tasks by generator scripts; each model is given the format guide and the request, and answers each task {{plan.samples:word}} times; the grader resolves the reference and the answer to their drawn state and compares them. Below the steps: the four checks that involve no model (Section 3.7). A *pair* is one request posed on both tracks. *Set-aside structures*: {{corpus.heldback.n_structures}} structures that the first version of the benchmark (public from May 2026) never used; their tasks are public too. *Task success*: the drawn state is exactly right. *Target score* (0 to 1): how exactly the answer marks out the requested atoms; any other drawing, such as a cartoon of the protein (a ribbon that traces the chain), is ignored. *F1*: how much of the drawn state is right, with partial credit. *Strict* and *valid-only* are the two main ways to average a score (Section 4.4).](generated/fig_pipeline.svg)

This paper makes four contributions.

1. **A corpus built by script** (Section 3): {{corpus.n_tasks}} tasks on
   {{corpus.n_structures}} structures in eight categories. In {{clin.n_face_value_wrong}} of
   its {{clin.n}} clinical requests, a model that copies the number from the variant name
   selects the wrong residue.
2. **A grader on drawn state** (Section 4), with three scores, tested on {{controls.n:,}}
   control answers whose verdict is known from how they were made.
3. **A paired design** (Sections 3.4 and 5.4). An answer is a MolViewSpec scene, which
   describes what the Mol\* viewer should load and draw (the *scene track*), or an ordered
   list of calls to the PDBe Mol\* viewer (the *call-list track*).
   {{corpus.n_twin_pairs}} requests are posed on both tracks, with the same target atoms, so
   that an error of content can be told apart from an error of format.
4. **A pilot that corrected the benchmark, and a fixed plan for the final run** (Sections 5 to 7). A pilot run exposed errors in our own benchmark (Table 13, rows 1 and 2), and the analysis of the final
   run (tables, comparisons and primary scores) was fixed before any model was called.
   ⟦PENDING: final run — one sentence stating the main result⟧
