## 1. Introduction

Molecular viewers are how structural biologists look at their data, and they are hard to
drive. To show one residue of one chain, a user must know the viewer's selection language, the
chain identifier, and which of several residue numbering schemes applies. Language models
promise to remove that barrier: the user says what they want, and the model writes the
commands. Several viewers now ship such assistants, or can be operated by one through a tool
protocol [@chimeraxmcp; @molstarprism; @navarro2026speak; @sun2024chatmol].

Whether these assistants are right is rarely measured, and a wrong answer is hard to see. One
request, which we follow through this paper, shows why:

> *"PDB entry {{ex.entry}}: the {{ex.gene}} ({{ex.protein}}) variant {{ex.variant}} is
> classified as {{ex.clinvar_classification}} in ClinVar. Show the residue it replaces as
> {{ex.color}} {{ex.rep}}."*

The variant name {{ex.variant}} counts residues along the UniProt sequence of human lysozyme:
tryptophan {{ex.uniprot_position}}. The Protein Data Bank (PDB) entry {{ex.entry}} numbers
the same chain from the start of the mature protein, {{ex.offset}} residues later. In the file,
that tryptophan is residue {{ex.auth_number}}, and residue {{ex.uniprot_position}} is a
serine. A model that selects residue {{ex.uniprot_position}} returns a clean picture of the
wrong amino acid, and nothing in the picture says so. The case is not unusual: a survey of the
PDB found that 38.6% of 176,507 entries contain proteins that are not numbered as their
UniProt sequences are [@faezov2021pdbrenum].

**Thesis.** Control of a molecular viewer by a language model can be measured exactly, and
without a second model as judge, if two conditions hold: each reference answer is computed
from the structure itself, and each answer is graded on what the viewer would draw, not on how
the answer is written.

MolBench is built on that thesis (Figure 1). The reference for the request above is not
written by a person. A script reads the variant from ClinVar [@landrum2018clinvar], maps its
UniProt position [@uniprot2025] to the residues of the entry with the SIFTS mapping
[@dana2019sifts], and confirms that the structure holds a tryptophan there. The grader then
resolves any answer to the atoms it would draw in that structure, with their representation
and colour, and compares this *drawn state* with that of the reference. Two answers that name
the same atoms in different ways receive the same score.

![**Figure 1. From public data to a score.** Top row: frozen public data are turned into tasks by generator scripts; a model answers each request once per sample; the grader resolves the reference and the answer to their drawn state and compares them. Bottom row: four checks that involve no model. A *pair* is one request posed on both tracks. F1, task success and target score are defined in Box 1.](generated/fig_pipeline.svg)

This paper makes four contributions, presented in this order.

1. **A corpus built by script** (Section 3): {{corpus.n_tasks}} tasks on
   {{corpus.n_structures}} structures in eight tiers of difficulty, including
   {{clin.n}} clinical-variant requests on {{clin.n_proteins}} proteins, of which
   {{clin.n_offset}} need a change of residue number. Every reference records how it was made
   and is tested against the structure.
2. **A grader on drawn state, with a measured error rate** (Section 4): three scores with
   plain definitions, and a control set of {{controls.n:,}} answers whose verdict is known from
   how they were made.
3. **A paired design** (Sections 3.4 and 5): {{corpus.n_twin_pairs}} requests are posed in two
   output formats with the same target atoms, so that an error of content can be told apart
   from an error of format.
4. **Evidence** (Section 6): a pilot run on {{oct.spec.n_models}} models that exposed a flaw in
   our own references and changed the design (Sections 6.6 and 7), and the tables that one
   final run will fill. ⟦PENDING: final run — one sentence stating the main result⟧

We write "computational intelligence (CI)" for what is often called artificial intelligence.
Box 1 defines the terms used throughout.

<div class="box">

**Box 1. Terms and notation.**

| Term | Meaning in this paper |
|:---|:---|
| Structure, entry | One deposited model from the Protein Data Bank (four-character identifier, such as {{ex.entry}}) or one predicted model from the AlphaFold Protein Structure Database. |
| Author numbering | The chain identifiers and residue numbers chosen by the depositors. This is what papers and most viewers show. |
| Label numbering | The chain identifiers and residue numbers assigned by the archive: residues are counted 1, 2, 3 … along each chain. |
| UniProt numbering | The position of a residue in the UniProt reference sequence of the protein. Variant names such as {{ex.variant}} use it. |
| SIFTS | Structure Integration with Function, Taxonomy and Sequences: the public residue-by-residue mapping between PDB entries and UniProt sequences. |
| Request | The plain-language instruction given to the model. |
| Scene | An answer in MolViewSpec: a description, in JSON (JavaScript Object Notation), of what to load and how to draw it. |
| Call list | An answer as an ordered list of calls to the PDBe Mol\* viewer (PDBe: Protein Data Bank in Europe). |
| Track | One of the two answer formats. *Scene track*: MolViewSpec scenes. *Call-list track*: viewer calls. |
| Draw | One representation type with one colour and one opacity, for example "grey cartoon, opaque". |
| Drawn state (final state) | For every atom of the structure, the set of its draws, plus a few facts about the whole scene (labels, distance lines, camera target). |
| Fact | One unit of the drawn state: all atoms that are drawn in the same way form one fact; each label or distance line is one fact. |
| F1 | How much of the drawn state is right, from 0 to 1: the harmonic mean of *recall* (the share of the reference's facts that the answer has) and *precision* (the share of the answer's facts that the reference has). |
| Task success | Yes or no: the drawn state is exactly right, with nothing missing and nothing extra. |
| Target score | From 0 to 1: are the atoms that the request is about drawn as asked, whatever else the answer did? |
| Valid output | An answer that parses as JSON and that the viewer accepts. |
| Strict / valid-only | Two ways to average a score. *Strict*: every output counts, an invalid one as 0. *Valid-only*: the mean over valid outputs. |
| Pair | One request posed on both tracks, with the same target atoms. |
| Held-back split | Tasks on structures that appear in no published task. |
| CI | Computational intelligence. |

</div>
