## 1. Introduction

Molecular viewers are how structural biologists look at their data, and they are hard to
drive. To show one residue of one chain, a user must know the viewer's selection language, the
chain identifier, and which of several residue numbering schemes applies. Language models
promise to remove that barrier: the user says what they want, and the model writes the
commands. Several viewers now ship such assistants, or can be operated by one through a tool
protocol [@chimeraxmcp; @molstarprism; @navarro2026speak; @sun2024chatmol].

Whether these assistants are right is rarely measured, and a wrong answer is hard to see. One
request, which we follow through this paper and always quote as it is in the task file, shows
why:

> *"{{ex.prompt}}"*

The variant name {{ex.name_in_prompt}} means that tryptophan (W) at position
{{ex.uniprot_position}} is replaced by arginine (R). The request asks for "the residue it
replaces": the tryptophan, which is what the structure contains. The position
{{ex.uniprot_position}} is counted along the UniProt sequence of human lysozyme, which begins
with {{ex.removed_what}}. The Protein Data Bank (PDB) entry {{ex.entry}} numbers the same chain
from the first residue of the mature protein, the protein that is left once that peptide has
been cut off. In the file, the tryptophan is therefore residue {{ex.auth_number}} (older papers
call the variant {{ex.mature_name}}), and residue {{ex.uniprot_position}} is a serine. A model
that selects residue {{ex.uniprot_position}} returns a clean picture of the wrong amino acid,
and nothing in the picture says so. The case is not unusual: a survey of the PDB found that
38.6% of 176,507 entries contain proteins that are not numbered as their UniProt sequences are
[@faezov2021pdbrenum].

**Thesis.** Control of a molecular viewer by a language model can be measured exactly, and
without a second model as judge, if two conditions hold: each reference answer is computed
from the structure itself, and each answer is graded on what the viewer would draw, not on how
the answer is written.

MolBench is built on that thesis (Figure 1). The reference for the request above is not
written by a person. A script reads the variant from ClinVar [@landrum2018clinvar], maps its
UniProt position [@uniprot2025] to the residues of the entry with the SIFTS mapping
[@dana2019sifts], and confirms that the structure holds a tryptophan there. The grader then
resolves an answer to the atoms it would draw in that structure, with their representation
and colour, and compares this *drawn state* with that of the reference. Two answers that name
the same atoms in different ways receive the same score.

![**Figure 1. From public data to a score.** Top row: frozen public data are turned into tasks by generator scripts; each model answers each request {{plan.samples}} times, independently; the grader resolves the reference and the answer to their drawn state and compares them. Bottom row: four checks that involve no model. A *pair* is one request posed on both tracks. *F1*: how much of the drawn state is right, with partial credit. *Task success*: the drawn state is exactly right. *Target score*: the requested atoms are drawn as asked, whatever else was drawn. *Strict* and *valid-only* are two ways to average (Box 1).](generated/fig_pipeline.svg)

This paper makes four contributions, presented in this order.

1. **A corpus built by script** (Section 3): {{corpus.n_tasks}} tasks on
   {{corpus.n_structures}} structures in eight tiers, grouped by what the model must know
   beyond the request. They include {{clin.n}} clinical-variant requests on
   {{clin.n_proteins}} proteins, of which {{clin.n_offset}} need a change of residue number.
   Every reference records how it was made and is tested against the structure.
2. **A grader on drawn state, tested against a control set** (Section 4): three scores with
   plain definitions, and {{controls.n:,}} control answers whose verdict is known from how
   they were made.
3. **A paired design** (Sections 3.4 and 5): {{corpus.n_twin_pairs}} requests are posed in two
   answer formats with the same target atoms, so that an error of content can be told apart
   from an error of format.
4. **A pilot that corrected the benchmark, and a fixed plan for the final run** (Sections 6
   and 7): a pilot run on {{oct.spec.n_models}} models exposed a flaw in our own references
   and changed the design, and one final run will fill tables whose shape is already set.
   ⟦PENDING: final run — one sentence stating the main result⟧

Box 1 defines the terms used throughout.

<div class="box">

**Box 1. Terms and notation.**

*Background terms, for readers from outside structural biology.*

| Term | Meaning |
|:---|:---|
| Residue, chain | A protein is a chain of amino acids. One amino acid in the chain is a *residue*; residues are numbered along the chain. A structure file names each chain with a short identifier, often one letter. |
| Structure, entry | A set of atom coordinates. An *entry* is one deposition in the Protein Data Bank, with a four-character identifier such as {{ex.entry}}; we use its first model. We also use predicted models from the AlphaFold Protein Structure Database. |
| Ligand | A small molecule bound to the protein. |
| Representation | A style of drawing: *cartoon* (a ribbon that traces the chain), *ball-and-stick*, *spacefill* (every atom as a full-size sphere), *surface*. |
| UniProt | The reference database of protein sequences. Each protein has an accession, such as {{ex.accession}}. |
| ClinVar | A public archive of human genetic variants. Laboratories submit their judgement of whether a variant causes disease, and ClinVar publishes one combined classification per variant. |
| Missense variant; {{ex.variant}} | A change of one amino acid into another. {{ex.variant}} (in full, {{ex.hgvs}}): the tryptophan (W) at position {{ex.uniprot_position}} becomes an arginine (R). |
| Mature protein | The protein after a leading segment, such as a signal peptide, has been cut off. Older literature often numbers residues from the first residue of the mature protein. |
| Mol\*, MolViewSpec | Mol\* is an open-source molecular viewer that runs in a web browser. MolViewSpec is a format, written in JSON (JavaScript Object Notation), that describes what Mol\* should load and draw. |
| Selection | The expression in an answer that picks atoms, for example "chain {{ex.auth_chain}}, residue {{ex.auth_number}}". |

*Terms of this paper.*

| Term | Meaning in this paper |
|:---|:---|
| Author numbering | The chain identifiers and residue numbers chosen by the depositors (in the structure file: `auth_asym_id`, `auth_seq_id`). This is what papers and most viewers show. |
| Label numbering | The chain identifiers and residue numbers assigned by the archive (`label_asym_id`, `label_seq_id`): residues are counted 1, 2, 3 … along each chain. |
| UniProt numbering | The position of a residue in the UniProt canonical sequence, counted from its first residue and so including any signal peptide. The variant names we use are in this numbering unless the request says otherwise (Section 3.1). |
| Offset | The difference between the author number of a residue and its UniProt number ({{ex.offset}} in the running example). |
| SIFTS | Structure Integration with Function, Taxonomy and Sequences: the public residue-by-residue mapping between PDB entries and UniProt sequences. |
| Request | The plain-language instruction given to the model. |
| Answer | What the model returns for one request. Each request is answered {{plan.samples}} times; each of these answers is a *sample*. |
| Scene | An answer in MolViewSpec: a description of what to load and how to draw it. |
| Call list | An answer as an ordered list of calls to the PDBe Mol\* viewer (PDBe: Protein Data Bank in Europe). |
| Track | One of the two answer formats. *Scene track*: MolViewSpec scenes. *Call-list track*: viewer calls. |
| Pair | One request posed on both tracks, with the same target atoms. The word is used for nothing else in this paper. |
| Target | The atoms that the request is about, stored with each task. |
| Draw | One representation type with one colour and one opacity, for example "grey cartoon, opaque". |
| Drawn state | For every atom of the structure, the set of its draws, plus a few facts about the whole scene (labels, distance lines, camera target). |
| Fact | One unit of the drawn state: all atoms that are drawn in the same way form one fact; each label or distance line is one fact. |
| F1 | How much of the drawn state is right, from 0 to 1, with partial credit: the harmonic mean of *recall* (the mean share of each of the reference's facts that the answer has) and *precision* (the mean share of each of the answer's facts that the reference has). |
| Task success | For one answer, yes or no: the drawn state is exactly right, with nothing missing and nothing extra. For a model, the share of its answers that succeed. The primary score. |
| Target score | From 0 to 1: are the target atoms drawn as asked, whatever else the answer did? An answer is *target-right* when its target score is exactly 1. |
| Unrequested context | Drawing that the request did not ask for, such as a cartoon of the protein behind a requested residue. |
| Valid answer | Scene track: the answer parses as JSON, is a scene, and is accepted by Mol\*. Call-list track: the answer parses as a JSON list that fits the call schema. |
| Strict, valid-only, repaired | Three ways to average a score (Section 4.4). *Strict* (primary): every answer counts, and an answer that cannot be shown scores 0. *Valid-only*: the mean over valid answers. *Repaired*: strict, after unparseable answers have been passed through an offline JSON repair. |
| Lookup tiers | The name-resolution and clinical-variant tiers, in which the answer needs one fact from a database: an entry identifier, or a residue number. |
| Held-back split | The tasks on {{corpus.heldback.n_structures}} structures that were set aside before generation and that no earlier MolBench task used. It is public, not secret (Section 3.6). |

</div>
