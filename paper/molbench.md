<!-- Built by paper/build.py from paper/sections/ and paper/generated/*.json (run numbers: October 2026 panel, PRELIMINARY). Do not edit: edit the sources. -->

# MolBench: Grading Language Models on What a Molecular Viewer Would Show

⟦PENDING: Dan — author list, affiliations, corresponding author⟧

*Draft for review. Every number in this paper is written by a script from the task files, the
frozen data or archived model answers; none is typed by hand. A cell or sentence marked
PENDING in double brackets waits for the one paid model run or for an author decision. The
results that exist today come from a pilot run in October 2026. They are reported in the boxed
Section 6.6 and are called pilot results wherever another section cites them.*

⟦PENDING: Dan — graphic for the table of contents, which the journal asks for⟧

## Abstract

Scientists ask language models to drive molecular viewers in plain words: "show the residue
changed by this variant". A wrong picture looks as polished as a right one. MolBench grades a
model on what the viewer would draw: which atoms, in which representation and colour. Each
reference answer is computed by script from the deposited structure, the SIFTS residue mapping
to UniProt, and ClinVar. The corpus has 797 tasks on 78
structures in eight tiers, from fully specified requests to clinical variants whose UniProt
positions must be mapped to the residues of a structure. 258 requests are
posed in two answer formats, a declarative scene and an imperative call list, to separate
errors of content from errors of format. The grader agrees with all 2,105 control
answers of known verdict, against which it was developed; two earlier text-comparing graders
rejected 42% and
54% of the correct ones. In a pilot run, clinical tasks
scored lowest although most answers drew the right residue: our references also drew a
background that no request had asked for. References now contain only what the request
states, and a target score reports on the requested atoms alone.
⟦PENDING: final run — main results on both tracks and the paired comparison, two sentences, which replace the two sentences on the pilot run so that the abstract stays within its limit⟧
Tasks, graders and model answers are open.

## 1. Introduction

Molecular viewers are how structural biologists look at their data, and they are hard to
drive. To show one residue of one chain, a user must know the viewer's selection language, the
chain identifier, and which of several residue numbering schemes applies. Language models
promise to remove that barrier: the user says what they want, and the model writes the
commands. Several viewers now ship such assistants, or can be operated by one through a tool
protocol [1, 2, 3, 4].

Whether these assistants are right is rarely measured, and a wrong answer is hard to see. One
request, which we follow through this paper and always quote as it is in the task file, shows
why:

> *"PDB entry 2NWD: the LYZ (Lysozyme C, UniProt P61626) variant p.W82R is classified as pathogenic in ClinVar. Show the residue it replaces as yellow spacefill spheres."*

The variant name p.W82R means that tryptophan (W) at position
82 is replaced by arginine (R). The request asks for "the residue it
replaces": the tryptophan, which is what the structure contains. The position
82 is counted along the UniProt sequence of human lysozyme, which begins
with the 18-residue signal peptide. The Protein Data Bank (PDB) entry 2NWD numbers the same chain
from the first residue of the mature protein, the protein that is left once that peptide has
been cut off. In the file, the tryptophan is therefore residue 64 (older papers
call the variant W64R), and residue 82 is a serine. A model
that selects residue 82 returns a clean picture of the wrong amino acid,
and nothing in the picture says so. The case is not unusual: a survey of the PDB found that
38.6% of 176,507 entries contain proteins that are not numbered as their UniProt sequences are
[5].

**Thesis.** Control of a molecular viewer by a language model can be measured exactly, and
without a second model as judge, if two conditions hold: each reference answer is computed
from the structure itself, and each answer is graded on what the viewer would draw, not on how
the answer is written.

MolBench is built on that thesis (Figure 1). The reference for the request above is not
written by a person. A script reads the variant from ClinVar [6], maps its
UniProt position [7] to the residues of the entry with the SIFTS mapping
[8], and confirms that the structure holds a tryptophan there. The grader then
resolves an answer to the atoms it would draw in that structure, with their representation
and colour, and compares this *drawn state* with that of the reference. Two answers that name
the same atoms in different ways receive the same score.

![**Figure 1. From public data to a score.** Top row: frozen public data are turned into tasks by generator scripts; each model answers each request 3 times, independently; the grader resolves the reference and the answer to their drawn state and compares them. Bottom row: four checks that involve no model. A *pair* is one request posed on both tracks. *F1*: how much of the drawn state is right, with partial credit. *Task success*: the drawn state is exactly right. *Target score*: the requested atoms are drawn as asked, whatever else was drawn. *Strict* and *valid-only* are two ways to average (Box 1).](generated/fig_pipeline.svg)

This paper makes four contributions, presented in this order.

1. **A corpus built by script** (Section 3): 797 tasks on
   78 structures in eight tiers, grouped by what the model must know
   beyond the request. They include 82 clinical-variant requests on
   25 proteins, of which 59 need a change of residue number.
   Every reference records how it was made and is tested against the structure.
2. **A grader on drawn state, tested against a control set** (Section 4): three scores with
   plain definitions, and 2,105 control answers whose verdict is known from how
   they were made.
3. **A paired design** (Sections 3.4 and 5): 258 requests are posed in two
   answer formats with the same target atoms, so that an error of content can be told apart
   from an error of format.
4. **A pilot that corrected the benchmark, and a fixed plan for the final run** (Sections 6
   and 7): a pilot run on 15 models exposed a flaw in our own references
   and changed the design, and one final run will fill tables whose shape is already set.
   ⟦PENDING: final run — one sentence stating the main result⟧

Box 1 defines the terms used throughout.

<div class="box">

**Box 1. Terms and notation.**

*Background terms, for readers from outside structural biology.*

| Term | Meaning |
|:---|:---|
| Residue, chain | A protein is a chain of amino acids. One amino acid in the chain is a *residue*; residues are numbered along the chain. A structure file names each chain with a short identifier, often one letter. |
| Structure, entry | A set of atom coordinates. An *entry* is one deposition in the Protein Data Bank, with a four-character identifier such as 2NWD; we use its first model. We also use predicted models from the AlphaFold Protein Structure Database. |
| Ligand | A small molecule bound to the protein. |
| Representation | A style of drawing: *cartoon* (a ribbon that traces the chain), *ball-and-stick*, *spacefill* (every atom as a full-size sphere), *surface*. |
| UniProt | The reference database of protein sequences. Each protein has an accession, such as P61626. |
| ClinVar | A public archive of human genetic variants. Laboratories submit their judgement of whether a variant causes disease, and ClinVar publishes one combined classification per variant. |
| Missense variant; W82R | A change of one amino acid into another. W82R (in full, p.Trp82Arg): the tryptophan (W) at position 82 becomes an arginine (R). |
| Mature protein | The protein after a leading segment, such as a signal peptide, has been cut off. Older literature often numbers residues from the first residue of the mature protein. |
| Mol\*, MolViewSpec | Mol\* is an open-source molecular viewer that runs in a web browser. MolViewSpec is a format, written in JSON (JavaScript Object Notation), that describes what Mol\* should load and draw. |
| Selection | The expression in an answer that picks atoms, for example "chain X, residue 64". |

*Terms of this paper.*

| Term | Meaning in this paper |
|:---|:---|
| Author numbering | The chain identifiers and residue numbers chosen by the depositors (in the structure file: `auth_asym_id`, `auth_seq_id`). This is what papers and most viewers show. |
| Label numbering | The chain identifiers and residue numbers assigned by the archive (`label_asym_id`, `label_seq_id`): residues are counted 1, 2, 3 … along each chain. |
| UniProt numbering | The position of a residue in the UniProt canonical sequence, counted from its first residue and so including any signal peptide. The variant names we use are in this numbering unless the request says otherwise (Section 3.1). |
| Offset | The difference between the author number of a residue and its UniProt number (18 in the running example). |
| SIFTS | Structure Integration with Function, Taxonomy and Sequences: the public residue-by-residue mapping between PDB entries and UniProt sequences. |
| Request | The plain-language instruction given to the model. |
| Answer | What the model returns for one request. Each request is answered 3 times; each of these answers is a *sample*. |
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
| Held-back split | The tasks on 15 structures that were set aside before generation and that no earlier MolBench task used. It is public, not secret (Section 3.6). |

</div>

## 2. Related work

Existing benchmarks that involve molecular viewers test agents that operate a desktop through
screenshots (ScienceBoard, OSWorld-Science), or score pictures with a judge model
(SciVisAgentBench). We found none that grades the atoms a viewer would draw against references
computed from the structure, and none that tests the mapping of residue numbers. Assistants
for molecular viewers exist, but their papers report no accuracy for viewer control.

### 2.1 Benchmarks that score control of scientific software

**ScienceBoard** [9] is the closest published benchmark. It has 169 tasks in
six domains, performed by agents that operate a desktop through screenshots and clicks. Its
biochemistry domain uses UCSF ChimeraX [10], and a task is checked by reading
the state of the application after the agent has finished. MolBench shares the idea of checking
the resulting state. It differs in four ways. It tests the step from request to commands
directly, with no desktop in between. Its references are computed by script and record their
origin. Its tiers are defined by what the model must know, up to clinical variants. And it
poses requests in two answer formats.

**SciVisAgentBench** [11] has 108 expert-written cases of scientific
visualization; its molecular cases use GROMACS and VMD. Outcomes are scored by a language-model
judge against written rubrics, with deterministic checks for some suites. The authors compared
the judge with 12 visualization experts and report an agreement among raters (Krippendorff's
alpha) of 0.669 and a correlation between judge and human scores of about 0.81. MolBench is
narrower and stricter: it covers only molecular viewers, and its scores need no judge model.

**OSWorld-Science** [12] follows the OSWorld desktop benchmark
[13] with 146 tasks over scientific applications, one of which pairs PyMOL with a
nuclear magnetic resonance package. Evaluators inspect application state and output files and
give partial credit. The overlap with MolBench is small: a molecular viewer is one application
among many, and the tasks test the operation of a graphical interface.

General benchmarks of tool use, such as ToolLLM [14] and tau-bench
[15], measure whether a model calls the right function with the right arguments.
Our call-list track has that shape. The difference is the check: a viewer call is right only
if its selection resolves to the right atoms in a particular structure.

### 2.2 Assistants for molecular viewers

**Speak to a Protein** [3] is an assistant that answers questions about a
protein while driving a browser viewer built on the Mol\* engine [16]. Its
evaluation covers question answering; the paper lists viewer operations as a task group and
reports no accuracy for them. **ChatMol Copilot** [4] is an agent for molecular
modelling that includes control of PyMOL. **ChimeraX** can be operated from a chat assistant
through a built-in tool server; its documentation notes that the assistant "will often make
mistakes" [1]. **VOICE** [17] and a speech interface for an immersive
molecular-graphics application [18] control molecular scenes by spoken language
and were evaluated with users, not with scored tasks. The Mol\* project has merged an optional
assistant and a command layer into its next viewer [2]; we found no published
benchmark from that work. A community tool that builds MolViewSpec scenes from chat
[19] states in its documentation that the residue numbers researchers take from
ClinVar, publications and mutation databases "are always author numbers". That holds for some
entries and fails for many [5]. It is the error our clinical tier is built to
detect.

### 2.3 The data and software MolBench stands on

MolViewSpec describes a molecular scene as a tree of typed nodes and is implemented as an
extension of the Mol\* viewer [16, 20, 21]. The
call-list track targets the PDBe build of Mol\* [22], which a notebook widget exposes
to Python [23]. Structures come from the Protein Data Bank [24] and, for
5 predicted models, from the AlphaFold Protein Structure Database [25, 26]. The mapping between UniProt residues and the residues of a structure
comes from SIFTS [8], as distributed by PDBe [27, 28]. Variants
and their clinical classification come from ClinVar [6], found through UniProt
[7]. Structure files are read with GEMMI [29].

The numbering problem at the centre of the clinical tier has been met from another side.
Vollmar and colleagues find residue mentions in the crystallographic literature and map them to
structures through SIFTS [30]. Their system reads papers; ours asks whether a
model can do the same mapping when it draws a scene. MiSI-Bench [31] asks
vision-language models questions about rendered images of molecules and finds them well below
human level, which is one reason our scores do not rest on a model that looks at pictures.

Statements in this section about what other work contains were checked against the cited
sources, and the notes of each check are in the repository. Where we say that a benchmark
lacks something, we mean that we did not find it in its paper.

## 3. Building the benchmark

A task is a request, a reference answer, the atoms the request is about (the *target*), and a
record of how the reference was made. No reference is written by hand. This section follows
the running example from public data to a finished task, and then describes the corpus as a
whole.

### 3.1 Frozen public data

**Structures.** All tasks draw on a fixed panel of 79 structures: 74 PDB
entries [24] and 5 predicted models from the AlphaFold Protein
Structure Database [25]. 78 of them are used in tasks; the
other one is reserved as the worked example in a prompt (Section 3.3). The panel was chosen
for coverage, not at random: small and large folds, proteins with bound small molecules, haem
groups and metal ions, proteins rich in disulfide bonds, nucleic acids, attached sugars,
membrane proteins, and entries whose functional assembly differs from the deposited model.
68 entries were solved by X-ray crystallography, 4 by
cryo-electron microscopy and 2 by nuclear magnetic resonance. The
5 predicted models are of p53, gamma-crystallin D, calmodulin-1, lysozyme and haemoglobin beta; each of these
proteins also has an experimental structure in the panel, and a predicted model is numbered as
UniProt is. Every feature we claim for an entry is verified in its file by the build script,
or the build fails. In 46 structures at least one residue has an author number
that differs from its UniProt number. Entries are limited to 15,000 atoms so
that they render quickly (2 larger entries are kept because earlier
tasks used them). The Supporting Information (SI, Section S3) lists the panel and its
selection rule.

**Disease proteins.** 27 human disease proteins are listed by
UniProt accession. For each, one PDB entry is chosen by a scripted rule (coverage of variant
positions, then resolution; SI Section S3). Whether an entry is numbered differently from
UniProt played no part in the choice. A variant may also be asked on any other panel structure
of the same protein: 6 proteins have more than one,
among them the 5 predicted models.

**Variants.** We use *missense* variants only: one amino acid replaced by another. Throughout,
the *classification* of a variant means ClinVar's combined (aggregate) germline classification
on a variation record, the record whose accession begins with VCV. The list of variants was
built in three steps; the counts are of variants removed and left.

| Step | Rule | Removed | Left |
|:---|:---|---:|---:|
| 1 | Single-residue missense variants of the 27 proteins that UniProt reports as pathogenic or likely pathogenic, with ClinVar as a source | | 3,352 |
| 2 | Keep if a ClinVar variation record lists the same amino-acid change and its aggregate classification is pathogenic, likely pathogenic or both | 657 | 2,695 |
| 3a | Remove if the only such record belongs to another gene | 44 | |
| 3b | Remove if the only such record is a haplotype (two changes on one chromosome) | 35 | |
| 3c | Remove if every such record has the review status "no assertion criteria provided" | 216 | 2,400 |

*Step 2* exists because UniProt lists a variant as pathogenic when any one submission to
ClinVar says so, whereas ClinVar's own classification combines all submitters. A candidate is
kept only if a ClinVar record that UniProt cites for it lists the same amino-acid change at
the same position and is classified "Pathogenic", "Likely pathogenic" or "Pathogenic/Likely
pathogenic". Step 2 removed 20% of the candidates, most of them
classified as conflicting or of uncertain significance. We did not compare transcripts: the
position is that of the UniProt canonical sequence, and the ClinVar record must list the
change at that position.

*Step 3* exists because a request says "the *GENE* variant ... is classified as pathogenic in
ClinVar", so the classification must rest on a record of that gene, about that one change,
with stated criteria. In step 3a the other gene is nearly always one that encodes the same
protein (*CALM2* or *CALM3* for calmodulin, *HBA2* for alpha-globin). In step 3b the record
describes two changes on one chromosome and says nothing about either alone. In step 3c no
submitter stated the criteria behind the classification.

The 2,400 variants left are the pool from which tasks are drawn. Two
decisions were made by name. One variant removed in step 3c is used all the same: lysozyme
p.Ile74Thr (I56T in the older literature), the first described cause of hereditary lysozyme
amyloidosis; it is outside the 2,400. One variant inside the
2,400 is never asked about, because its clinical meaning is easily misread:
APOE p.Arg154Ser, the Christchurch variant. Tasks exist for 25 of the
27 proteins; for the other
2 the steps above left at most one variant, and no
task was made. The variant lists and their classifications were read from UniProt and ClinVar
on 2026-11-12; the kind and review status of each ClinVar record were read
on 2026-11-16.

**Atom tables and residue mapping.** For each structure we store two frozen tables. The *atom
table* lists every atom with its chain and residue in both author and label numbering; it is
built from the deposited file and compared with what the viewer itself selects (Section 3.7).
The *mapping table* holds the SIFTS correspondence between each observed residue and its
UniProt position. Generators and graders read only these tables. Nothing is fetched while a
task is built from the tables, graded or loaded.

### 3.2 From data to a task: the running example

The clinical generator produced the running example in six steps.

1. **Variant.** From the pool it draws LYZ W82R (UniProt P61626,
   p.Trp82Arg; "Familial visceral amyloidosis, Ostertag type (AMYLD2)"; classified pathogenic). ClinVar holds
   2 records of this protein change, one for each DNA change that
   causes it (VCV000014376, NM_000239.3(LYZ):c.244T>C (p.Trp82Arg); VCV000014378, NM_000239.3(LYZ):c.244T>A (p.Trp82Arg)). Their review status is "criteria provided, single submitter";
   we return to what that means in Section 9.
2. **Structure.** The panel entry for P61626 is 2NWD, human lysozyme at
   1.04 Å resolution.
3. **Mapping.** The mapping table says that UniProt positions
   19–148 are author residues
   1–130 of author chain X: an offset of
   18, the length of the signal peptide. Position 82 is
   therefore author residue 64 (label chain A, label residue
   64).
4. **Identity check.** The atom table must hold the amino acid of the reference sequence at
   that residue. It does: Trp64, 24 atoms
   (14 and 10 hydrogens, which this entry
   contains). Had the structure carried an engineered substitution there, the variant would
   not be offered for this entry.
5. **Wording.** A seeded random choice picks one of the template's three wordings, the colour
   (yellow) and the representation (spacefill spheres). The request names the entry, the gene,
   the UniProt accession and the variant. It never says which residue of the entry is meant.
6. **Reference, twice.** The script writes the reference scene (author chain
   X, author residue 64, yellow spacefill spheres) and the
   reference call list (load the entry; draw UniProt P61626 position
   82 as yellow spacefill spheres). It then confirms that both resolve to
   the same 24 atoms, and stores them as the target of both tasks. On the
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
structure, the residues, the colours and the wording. The corpus has 129
templates. No template supplies more than 12% of a tier's
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
- **Clinical variant.** As in the running example. There are 82 tasks per track, on
  25 proteins and 31 structures. Two properties of a task
  matter for the results, and they are not the same property.
  *Split A: would an answer that copies the number in the variant name be right?* Yes in
  34 tasks, no in 48. This is the primary
  split.
  *Split B: does the author number of the target differ from its UniProt number?* Yes in
  59 tasks (72%), by 1 to
  216 residues; no in 23.
  The splits differ because 13 requests use a traditional name that is
  counted along the mature protein, the form found in older literature (transthyretin V30M,
  which is p.Val50Met), and say so. In 12 of these the entry is
  numbered in the same traditional way, so the number in the name is the author number
  although the UniProt number is not. In the remaining 1 the
  structure is a predicted model numbered as UniProt is, so the traditional number is wrong
  there. Split A therefore has 22 +
  12 = 34 tasks on its "yes" side.
  Further facts: in 25 tasks the author chain identifier differs from
  the label chain identifier; 46 requests state the UniProt
  accession, as the running example does; 29 also ask, in words, for a
  cartoon of the structure; and 10 ask for the helix or strand that contains the
  residue, as annotated in the entry, together with the residue. 20 tasks
  form 10 sets of two *matched tasks* that ask the same variant on two
  structures of one protein; in 8 of these sets one structure has an
  offset and the other, always a predicted model, has none.
- **Follow-up turn.** The model receives a start state and an edit request ("make the magenta
  chain plum") and returns the complete new state. Only the resulting drawn state is graded,
  so an answer that makes the edit but drops something from the start state, such as the
  colour of another chain, fails. In 10 scene tasks and
  8 call-list tasks the right answer is to change nothing.
- **Several right answers.** The request leaves one countable thing open. "Colour Lys29
  yellow" in an insulin entry with two B chains can mean either copy or both. The script lists
  every *accepted answer* (a median of 3 per task on the
  scene track), and an answer that matches any one of them is right.
- **Viewer settings.** Settings that only the call-list format can express, such as electron
  density maps, background and spin.

We call name resolution and clinical variant the *lookup tiers*. In both, what the request
leaves out is one fact from a database: which entry holds the protein, or which residue number
the variant has in the entry. Only these two tiers have a grounding pack (Section 5.2).

**Table 1. The corpus.** Tasks per tier and track, written as total (public + held back; Section
3.6). *Pairs*: requests posed on both tracks with the same target atoms. A dash means that the
format cannot express the tier.

| Tier | What is asked | Scene track (public + held back) | Call-list track (public + held back) | Pairs |
|:---|:---|---:|---:|---:|
| Translation | Everything needed is in the request; write it in the format. | 73 (55 + 18) | 178 (138 + 40) | 62 |
| Structure-grounded | The request names a feature (the ligand, the disulfides); its atoms must be found in the structure. | 63 (52 + 11) | 63 (52 + 11) | 63 |
| Interactions | Named atoms and a measurement or contact between them. | 40 (32 + 8) | – | – |
| Name resolution | The structure is named by protein, not by identifier. | 39 (32 + 7) | – | – |
| Clinical variant | A variant in UniProt numbering must be mapped to the residues of the structure. | 82 (63 + 19) | 82 (63 + 19) | 82 |
| Follow-up turn | A start state plus an edit request; the full new state is returned. | 58 (50 + 8) | 44 (34 + 10) | 36 |
| Several right answers | The request leaves one countable thing open; several drawn states are right. | 26 (21 + 5) | 15 (11 + 4) | 15 |
| Viewer settings | A viewer setting that only the call-list format can express. | – | 34 (29 + 5) | – |
| **All** | | **381** (305 + 76) | **416** (327 + 89) | **258** |

The 797 tasks (381 scene, 416 call-list) use
78 of the 79 panel structures. The one unused entry is the worked
example in the call-list prompt, which must not also be a task. No structure appears in more
than 6 tasks of one tier and track.

### 3.4 The same request in two formats

A wrong answer has two possible causes: the model did not know which atoms were meant, or it
knew and could not write them in the format. One format cannot separate the two. MolBench
therefore poses 258 requests (68% of the scene
tasks) on both tracks, with identical wording and the same target atoms (Figure 3).

The two formats differ in kind. A MolViewSpec scene [20] is *declarative*: a tree
that states what to load, which atoms form a component, and how each component is drawn.
Nothing is on screen unless the scene says so. A call list is *imperative*: an ordered list of
calls to the PDBe Mol\* viewer, version 3.3.2 [22]. The viewer starts with the whole
structure drawn in a default style, and each call changes that state, so order matters.

The formats also differ in what they demand for a clinical request, and we state this openly
because it shapes the comparison. The viewer behind the call-list track can select a residue by
UniProt accession and position and does the mapping itself. A scene has no such selector: the
model must produce author or label numbers. The running example's call-list reference uses the
UniProt selector; its scene reference uses author residue 64. Either numbering
is accepted on either track if it resolves to the right atoms. On the call-list side of a
clinical pair, a model can thus be right without knowing any residue number: when the request
states the accession (46 of the 82 clinical requests), it
only has to pass the accession and the position on to the right call; otherwise it must also
know the accession.

![**Figure 3. One request, two formats, the same target atoms.** The scene and the call list are shown in shortened form. Below: for each model, every pair falls into one of four cells by whether each side is right. The primary comparison counts a side as right when its target score is 1; it is repeated with task success (Section 5.4). McNemar's test compares the two shaded cells, in which the model was right in one format only.](generated/fig_twins.svg)

Pairs exist in five tiers: translation (62), structure-grounded
(63), clinical (82), follow-up
(36) and several right answers (15).
123 scene tasks have no partner on the call-list track. Either the
call-list format cannot draw what they ask for (a distance line, a text label, a transparent
surface), or they are name-resolution tasks, in which the model chooses the entry and the
call-list grader has no atom table for an entry outside the panel.

The two formats do not treat unrequested context alike, and that decides how the pairs are
compared. A scene starts from an empty screen and has to list everything it draws, so a scene
that adds a cartoon that the request did not ask for has drawn something extra and is not
exactly right. The call-list viewer draws the whole structure as soon as it loads, so a call
list that colours one residue and leaves the rest of the default view on screen has added
nothing and is right. The default view must go only where the request says so: in
15 pairs the request asks for something to be shown alone or to
be removed ("Load 1AKE and show only chain A, as a teal cartoon."), and the call list must then switch off part of
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

*Held-back split.* 15 structures were set aside before
generation. No public task uses them, and no MolBench task published before November 2026
used them. The 165 tasks on them (21% of the
corpus) form the *held-back split*. The split is not a secret test set: the corpus was
developed in a public repository, so these tasks were online for some days before the final
run. Nearly all tasks in both splits are new. The split therefore does not compare seen tasks
with unseen tasks. It compares structures that earlier MolBench tasks had used with structures
that none had used. Three held-back structures share a protein with a public structure. We
report the difference between the splits with an interval and do not test it, because the
split is small (Section 9).

*Wording.* To measure sensitivity to wording, 30 requests of
the public split have two further phrasings each, a terse one and an indirect one, with the
same reference. For example, the request "Add chain B too, as a cartoon in grey." also exists as
"chain B too, grey cartoon" and as "Could I see chain B as well? A grey cartoon would be fine.".
11 of the 30 requests are pairs, so
they are 41 tasks, and two further phrasings of each give
82 additional task files. These are not counted in Table 1.

### 3.7 Checks on the corpus

Four checks involve no model (Figure 1, bottom row).

- **Reference against structure.** Every reference must select at least one atom, must name the
  residue that the generator intended, and must grade as exactly right against itself. Every
  accepted answer must do the same.
- **Atom tables against the viewer.** Selections were read back from the running viewers. For
  the scene track, Mol\* 5.9.0 was run without a display and asked which atoms each
  representation holds. For the call-list track, 234 call lists, a
  sample of the control set (Section 4.5), were replayed in PDBe Mol\* 3.3.2 and each
  selection was compared atom for atom: all agreed. Loading a structure with no further call
  was compared in the same way for 73 of the
  73 PDB entries used in tasks. Selections by UniProt number were not part
  of this replay (SI Section S4.8).
- **Grader against a control set.** The grader is run on 2,105 answers whose
  verdict is known (Section 4.5).
- **Format rules.** One script validates every task file against the written task format, and
  the run does not start unless every check passes.

## 4. Grading on drawn state

### 4.1 From an answer to a drawn state

An answer is graded by what the viewer would show, not by how the answer is written. The
grader turns the reference and the answer into a *drawn state*: for every atom of the
structure, the set of its *draws* (a representation type with a colour and an opacity), plus a
few facts about the scene as a whole. It does so with the frozen atom tables and with the rules
of the viewer itself, which we read back from the running viewer and did not take from
documentation. Two examples of such rules: a cartoon draws only polymer residues, so a cartoon
of "everything" and a cartoon of "the polymer" are the same drawing; and a cartoon requested
for a ligand is drawn by Mol\* as ball-and-stick, and is graded as that. No browser runs and
nothing is fetched while grading.

The drawn state is cut into *facts* of equal weight. All atoms that carry the same set of
draws form one fact. "The protein as a grey cartoon, with one residue also as red
ball-and-stick" is two facts: the atoms of that residue (grey cartoon and red ball-and-stick),
and all other protein atoms (grey cartoon only). Each text label, each distance line and the
camera target, when the request asks for one, is a further fact. Loading the right entry earns
nothing by itself; on an entry that the task does not accept nothing can be compared and every
score is 0. One tier is a partial exception to grading on drawn state: a name-resolution
answer on an accepted entry outside the panel has no atom table to be resolved on, and is
compared as written (Sections 3.3 and 9).

On the call-list track the grader replays the calls in order, following the behaviour of PDBe
Mol\* 3.3.2, and compares the drawn state that they end in. Because that viewer draws the whole structure as soon
as it loads, the facts of a call-list answer are its *differences from a bare load*. Order
matters, as it does in the viewer: a later call can undo an earlier one, and the answer is
graded on where it ends. SI Section S4 lists every rule on both tracks.

### 4.2 Three scores

Each answer receives three scores. They answer different questions, and Section 4.3 shows them
parting on the running example.

**F1: how much of the drawn state is right?** *Recall* is the mean, over the reference's
facts, of how much of each fact the answer has. *Precision* is the mean, over the answer's
facts, of how much of each the reference has. F1 is their harmonic mean, from 0 to 1. For a
fact, which is a group of atoms drawn alike, "how much" is the share of its draws that the
other side also has; a draw with the right representation and the wrong colour counts half.
Missing drawing therefore costs recall, and unrequested drawing costs precision. Section 4.3
works one case through.

**Task success: is the drawn state exactly right?** For one answer, task success is yes or
no: yes if recall and precision are both 1 on an accepted structure, so that every fact of the
reference is present and the answer has no other. For a model, the *task success rate* is the
mean over tasks of the share of the task's 3 answers that succeed. This is the
primary score, because a viewer scene is either the one that was asked for or it is not. Two
further summaries are used and always named: *all-3*, the share of tasks on
which every answer succeeds, and *majority*, used only in the paired analysis, where a side of
a pair counts as right if at least two of its three answers are (Section 5.4).

**Target score: are the requested atoms right, whatever else was drawn?** Each task stores
its target, the atoms the request is about. The target score, from 0 to 1, compares only how
those atoms are drawn. It gives credit for each requested draw that the answer has, and half
credit for the right representation in the wrong colour. Extra drawing is treated by its
extent. A draw that repeats the requested drawing on atoms outside the target lowers the score
(colouring the whole chain when one residue was asked for). So does an unrequested draw that
is confined to the target atoms (sticks on the residue in addition to the requested spheres).
A draw that covers far more than the target, such as a cartoon or a surface of the whole
chain, is unrequested context and is ignored, even where it would hide the target in a real
picture; task success catches that case. An answer is *target-right* when its target score is
exactly 1. The target score separates "found the wrong residue" from "found the right residue
and added context".

**Unrequested context, stated once.** On the scene track the screen starts empty, so anything
drawn beyond the request counts against precision and task success. On the call-list track
the viewer starts with the whole structure drawn, only changes from that default view are
graded, and leaving the default view in place costs nothing (Section 3.4). The target score
ignores unrequested context on both tracks. Two consequences follow. Within a track, models
are ranked by the task success rate, and the target score is reported beside it. Between the
two formats, models are compared on the pairs only, and first on the target score
(Section 5.4).

When a task lists several accepted answers (Section 3.3), an answer is graded against each,
and the best result counts. The two tracks share these definitions; the arithmetic of F1
differs slightly between them (SI Section S4), and task success means the same on both.

### 4.3 The running example, graded

Figure 4 and Table 2 grade several answers to the running example. The reference draws
Trp64 of chain X as yellow spacefill spheres, and
nothing else.

![**Figure 4. Drawn-state grading of three answers to the running example.** Each panel shows a stretch of chain X in author numbering, the facts of the answer's drawn state, and its scores. *Fact*: all atoms that are drawn in the same way. *Recall*: the mean share of each of the reference's facts that the answer has. *Precision*: the mean share of each of the answer's facts that the reference has. *F1*: their harmonic mean. *Task success*: drawn state exactly right. *Target score*: the requested atoms drawn as asked, whatever else was drawn.](generated/fig_grading.svg)

**Table 2. Answers to the running example and their scores**, computed by the benchmark's
grader. *F1*: how much of the drawn state is right (0 to 1). *Task success*: the drawn state
is exactly right. *Target score*: the requested atoms are drawn as asked, whatever else was
drawn (0 to 1).

| Answer | F1 | Task success | Target score |
|:---|---:|:---|---:|
| **Scene track** | | | |
| Reference: author chain X, author residue 64, yellow spacefill spheres | 1.00 | yes | 1.00 |
| The same residue named by label numbering (label chain A, residue 64) | 1.00 | yes | 1.00 |
| Number in the variant name used as the author number (Ser82) | 0.00 | no | 0.00 |
| Right residue, drawn red | 0.50 | no | 0.50 |
| Right residue, plus a grey cartoon of the protein that the request does not ask for | 0.40 | no | 1.00 |
| Wrong residue, plus the grey cartoon | 0.00 | no | 0.00 |
| **Call-list track** | | | |
| Reference: UniProt P61626 position 82, resolved by the viewer | 1.00 | yes | 1.00 |
| The same residue named by author numbering (chain X, residue 64) | 1.00 | yes | 1.00 |
| Number in the variant name used as the author number (Ser82) | 0.00 | no | 0.00 |
| Right residue, drawn red | 0.50 | no | 0.50 |
| Load only, no further call | 0.00 | no | 0.00 |

Three points follow. First, an answer may name the residue in any numbering: the second row of
each track is written differently from the reference and scores the same, because it draws the
same atoms. Second, the answer that takes the "82" of
p.W82R at face value draws Ser82,
shares no atom with the reference, and scores 0 on all three measures. Third, the answer that
finds the right residue and adds a grey cartoon of the protein has a target score of
1.00 but an F1 of 0.40 and no task success: it
drew a cartoon over the whole chain that the request did not mention.

The F1 of that third answer is worked out as follows (Figure 4, Answer B). The answer has two
facts. Fact 1 is the atoms of Trp64; they carry two draws, the
grey cartoon and the yellow spacefill spheres, and the reference has one of the two: one half.
Fact 2 is all other atoms of the protein; they carry only the grey cartoon, and the reference
has none of it: zero. Precision is the mean of the two, 0.25.
Recall is 1.00, because the reference's one fact is fully present.
F1, their harmonic mean, is 0.40.

An F1 of 0.40 alone does not say what went wrong: a half-right residue
with no context could score in the same range (the right residue drawn red scores
0.50). The target score of 1.00 says that the
residue is right and that the loss is unrequested context.

### 4.4 Invalid answers

Some answers cannot be shown at all. Every answer gets one *outcome*, and two things must be
kept apart.

- An answer *cannot be shown* if it contains no parseable JSON of the right outer shape or,
  on the scene track, if it is not a scene or is rejected by the validation of Mol\* 5.9.0
  itself, run without a display. Such an answer scores 0 on all three scores.
- A call list *breaks the schema* if it parses as a JSON list but holds an unknown call or a
  wrongly typed field. The viewer ignores such parts and carries on, and so does the grader:
  the list is replayed as the viewer would treat it and keeps the scores it earns. It is not
  counted as a valid answer.

A *valid answer* is thus, on the scene track, one that Mol\* accepts and, on the call-list
track, a JSON list that fits the call schema. An answer cut off at the token limit is counted
apart from a malformed one. SI Table S4 lists every outcome with its score.

Scores are averaged in three named ways.

- **Strict** (primary): every answer counts. An answer that cannot be shown scores 0; a call
  list that breaks the schema keeps the scores it earns. This is what a user of the bare
  model would experience.
- **Valid-only**: the mean over valid answers. This separates "wrote a loadable answer" from
  "the answer is right".
- **Repaired**: a counterfactual. Each answer that is not parseable JSON is passed through an
  offline JSON repair library [32] and graded again. No model is called. The repaired
  score is reported beside the strict score and never replaces it.

### 4.5 How well the grader itself works

A grader that compares drawn states can still be wrong: it may fail a correct answer that is
written in an unexpected way, or pass a wrong one. We test this with a *control set* of
2,105 controls (Table 3). A control is a reference and one answer whose verdict is
known from how the answer was made. The answer is one of three things.

- **Identical**: the reference itself. It must pass.
- **Equivalent**: the reference rewritten so that the viewer shows the same. Examples: a
  residue range as a list of residues; label numbering in place of author numbering where the
  two name the same atoms; a colour as a hexadecimal code; one component or several; on the
  call-list track, a wrong step that a later step undoes. It must pass.
- **Wrong**: an answer that shows something else. Examples: the neighbouring residue; the other
  chain; the UniProt number used as the author number on a structure where they differ; a
  named shade of the colour that lies outside the colour tolerance (Section 4.6); a missing
  or an extra component; another copy of the ligand. It must fail.

A *false pass* is a wrong answer graded as a task success. A *false fail* is an identical or
equivalent answer graded as not a success.

The grader makes no error on the control set, and this must be read with care. We developed
the grader against the controls and corrected it until it agreed with every one. The zeros
therefore show that the stated rules are implemented and stay implemented: the control set is
run as a test on every change. They are not an estimate of how often a way of writing an
answer that we did not foresee is misjudged. That estimate needs people, and is the purpose of
the rating study (Section 5.5).

**Table 3. Error rate of the grader on the control set.** *False pass*: wrong answers graded as
task success, out of all wrong answers. *False fail*: identical or equivalent answers graded as
not a success, out of all such answers. *Earlier grader*: the grader that this work replaces on
each track (for the scene track, a comparison of scene trees path by path; for the call-list
track, a comparison of call sequences field by field), with a score of exactly 1 read as
success.

| Track | Controls | Structures | Kinds of equivalent / wrong answer | False pass | False fail | Earlier grader: false pass | Earlier grader: false fail |
|:---|---:|---:|---:|---:|---:|---:|---:|
| Scene | 1,110 | 78 | 24 / 24 | 0 of 480 | 0 of 630 | 13 of 480 (3%) | 264 of 630 (42%) |
| Call list | 995 | 74 | 22 / 21 | 0 of 420 | 0 of 575 | 75 of 420 (18%) | 311 of 575 (54%) |

Two things keep the control set honest. First, the verdicts do not come from the grader. For
the scene track, the two scenes of each control were loaded in Mol\* 5.9.0 and the atoms,
colours and opacities of each representation were read back. This was done on the control set
as it then stood, 1,030 scene controls. For
890 of them the drawing can be read back, and in all
890 the viewer drew the same for the controls that must pass and
something different for the controls that must fail. The other
140 are of kinds that cannot be read back this way, such as camera
target and label text. 80 scene controls added since then
have not been read back in the viewer. For the call-list track, the call lists of a sample of
controls (234 lists) were replayed in PDBe Mol\* 3.3.2, and the
state they ended in matched the grader's replay in every case. Second, the earlier graders
give the scale of the problem that the control set detects: the scene grader used in our pilot
run failed 42% of correct control answers, and the first
call-list grader passed 18% of wrong ones. SI Section S5
lists every kind of control with its counts.

### 4.6 What is deliberately not graded

Camera position is never graded. If the request asks to focus on something, the grader compares
which residues the camera frames; if it does not, a focus in the answer is not counted. Sizes,
line widths and label styling are not graded. Two colours count as the same if their red, green and
blue values (0 to 255) each differ by at most 32. We measure the distance
between two colours as the largest of these three differences. Requests use a palette of
19 named colours. Its two closest colours (plum and hotpink) are
55 apart, so no palette colour can pass for another, and a
lighter or darker named shade is a different colour. In the pilot run, 2,227
of 2,303 comparable colour values were exactly the requested colour,
and each of the other 76 was at least 58 away
from it, so the tolerance decided no case.

## 5. Experimental setup

One run fills every result in Section 6. Its plan is fixed in a single manifest file before any
model is called: the corpus version and its hash, the models and their prices, the prompting
conditions, the number of samples and the limits. SI Section S6 reproduces it.

### 5.1 Models

The panel is set by a written rule, not by results. The core panel is every model on the
project's public results table of October 2026: 16 language models,
13 with openly available weights and 3 without, so that
old and new numbers can be compared. 15 of them ran in the October pilot
of the scene track (Section 6.6); the other, mistral-small-2603, could not be reached
on that day and had earlier call-list results only. Up to 5 further
models are *optional*: the current flagship model of each major provider, and the largest
model with public weights, as listed on the day the prices were recorded in the manifest
(2026-11-16). They are run only if the budget allows (Section 5.6), which is decided
before any result exists, and they are marked † in the tables. No model is added or dropped after results are seen. A
*keyword script* that uses no model is run on both tracks as a floor: it maps words in the
request to fixed answers by rule. SI Table S6 lists every model.

### 5.2 Prompting conditions

Every model receives a system prompt and the request, and returns one answer. Models cannot
look anything up, ask a question back, or see a rendered result.

**Table 4. Prompting conditions.** The first is the *main condition*, from which all main
results come. *Format reference*: a frozen text that documents the answer format. *JSON mode*:
a provider option that forces syntactically valid JSON. *Grounding pack*: the result of an
offline lookup, appended to the request: the chains of the structure, its residue ranges in
both numberings, the UniProt mapping and, for a clinical task, the residue that each named
variant maps to. *Samples*: answers per model and task.

| Condition | What the model is given | Run on | Samples |
|:---|:---|:---|---:|
| **Format reference** (main condition) | A short instruction, the rule for the answer ("answer with one JSON value and nothing else") and the format reference | all models, all tasks, both tracks | 3 |
| Format reference + JSON mode | The same, with JSON mode switched on | the 15 core models whose provider offers it, all tasks, both tracks | 1 |
| Format reference + grounding pack | The same, with the task's grounding pack appended to the request | all models; the lookup tiers (name resolution, clinical variant), scene track | 3 |
| No format reference | The instruction and the rule for the answer only | 3 models (claude-haiku-4-5, deepseek-v3.2, qwen3-30b-a3b-instruct-2507), the same as in the pilot run; scene track | 3 |

A grounding pack never contains a scene, a colour or a representation. But for a clinical
task it contains the mapped residue, and for a name-resolution task a list of entries. The
grounding-pack condition is therefore an upper bound: the lookup has been done and its result
handed over. It is not a test of whether a model can use raw lookup tables. For the running
example the pack states that UniProt 19–148 are
author residues 1–130 of chain X (SI
Section S1). No prompt was tuned on benchmark tasks, and the worked example in each prompt
uses a structure that no task uses. SI Section S7 gives both system prompts.

### 5.3 Sampling

Each model answers each task 3 times in the main condition, at the provider's
default temperature. The limit on the length of an answer is 8,000 tokens. A
malformed answer is scored as it stands and is not retried; only transport errors are retried.
Every raw answer is archived with its token counts, finish reason and cost.

### 5.4 Statistics

- **Per-model scores** are means over tasks of the mean over the task's 3
  answers. For task success this is the task success rate; the all-3 summary
  (the share of tasks on which every answer succeeds) is reported beside it (Section 4.2).
  Means over models leave the keyword script out.
- **Intervals** are 95% bootstrap intervals [33] with 10,000
  resamples. Whole structures are resampled, not single tasks, because tasks on one structure
  share its difficulties.
- **Paired comparison of formats.** For each model and pair, a side counts as right when at
  least two of its three answers are right (the majority summary of Section 4.2). "Right" is
  taken two ways. The primary comparison uses the target score: an answer is right when it is
  target-right, that is, when its target score is exactly 1. This is the same test in both
  formats. The secondary comparison uses task success, which is not the same test in the two
  formats (Section 3.4), and is shown beside the first. Pairs right on one side only are
  compared with McNemar's exact test [34]. We report the four counts for every
  model. We repeat the analysis without the 15 pairs in which
  the call list must switch off part of the default drawing (Section 3.4), and without the
  clinical pairs, in which the call-list viewer can do the mapping itself (Section 3.4).
- **Planned comparisons**, each as a difference in task success rate with an interval: public
  against held-back split; full against terse and indirect wording; with and without JSON
  mode; with and without grounding pack; clinical tasks in which the number in the variant name
  is, or is not, the author residue number. Totals of the two tracks are not compared with
  each other: the tracks differ in their mix of tiers and in the length of the answer, so the
  formats are compared on the pairs only.
- **What F1 is read against.** F1 has a floor that needs no skill: a scene with nothing but a
  protein cartoon, or a follow-up's start state returned unchanged, shares most of its drawing
  with the reference. The task success rate is therefore the primary score and the target
  score is reported beside it; F1 is shown with the keyword script beside it, which marks
  that floor.

The planned comparisons are the six differences with intervals of Table 11. The McNemar tests
are one per model; we read each as a description of that model and not as a family of tests.
We do not correct for multiple comparisons, and we report every count.

### 5.5 Human check of the grader

The grader's verdict is also checked against people. After the run, volunteers will see
*picture comparisons*: two pictures side by side, a reference and a model answer, rendered
from the same camera and framed on the target atoms. They say whether the two show the same
thing. The design calls for 300 picture comparisons with
2 raters each. People's verdicts are compared with the grader's task
success. A further 40 picture comparisons are of answers that the
grader counts as exactly right although their pictures are not identical pixel for pixel;
people should call these the same. The study also tests an *image judge*: a vision-language
model that is shown the same two pictures and asked the same question. The image judge
contributes to no score in this paper. A smaller pilot of the study has been run (Section 6.6).

### 5.6 Reproducibility

One command performs the run from the manifest. It does not start if the projected cost is
above a cap in US dollars that the manifest states, and it stops if spending would pass it. One command rebuilds every table, figure and number in this paper from the archived
answers. A rehearsal with a mock model exercises the whole path at no cost. Grading needs no
network access and no paid service.

## 6. Results

Sections 6.1 to 6.5 show every result table in its final shape. The cells wait for the one
paid run and are filled by script from its archive; the layout, the captions and the
definitions will not change. In this draft the two tables with one row per model show their
first rows only. Section 6.6 is different: it reports, in a box, what a pilot run in October
2026 showed. Those numbers are real but come from an older corpus, and they are kept apart
from everything else.

![**Figure 5. The result figures that the final run will fill.** No data are shown. **A**: task success rate per model on both tracks, with 95% intervals; *task success rate* is the share of answers whose drawn state is exactly right, and an answer that cannot be shown counts as wrong (strict). **B**: for each model, its pairs split by which side was right; a side is *right* when at least two of its three answers have a target score of 1. **C**: task success rate and target score per tier, valid-only (the mean over valid answers), so that the gap between the two marks shows unrequested drawing and not unparseable answers; *target score* asks only whether the requested atoms are drawn as asked.](generated/fig_result_shapes.svg)

### 6.1 Models on both tracks

**Table 5. Scene track, main condition (format reference).** One row per model; † marks an
optional model. *Valid answers*: share of answers that parse and that the viewer accepts. *F1*:
how much of the drawn state is right (0 to 1). *Task success*: share of answers whose drawn
state is exactly right (the task success rate). *Target score*: whether the requested atoms
are drawn as asked, whatever else was drawn (0 to 1). *Strict*: every answer counts, and an
answer that cannot be shown scores 0. *Valid-only*: the mean over valid answers. *All 3
samples right*: share of tasks on which every one of the three answers is exactly right. *Cost*: US dollars for all calls of the model in this
condition, at list price. Intervals (95%, structures resampled) will be given with each score.

| Model | Weights | Valid answers | F1 (strict) | Task success (strict) | Target score (strict) | F1, valid-only | Tasks with all 3 samples right | Cost (USD) |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|
| Keyword script (no model) | – | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| claude-haiku-4-5 | closed | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| deepseek-v3.2 | open | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| … 19 further rows, one per model of SI Table S6 | | ⟦PENDING: final run⟧ | | | | | | |

**Table 6. Call-list track, main condition.** Same columns and definitions as Table 5, except
that a *valid answer* is a JSON list that fits the call schema, and a call list that breaks
the schema keeps, under *strict*, the scores it earns when replayed (Section 4.4).

⟦PENDING: final run — the table for the call-list track, in the shape of Table 5⟧

### 6.2 Tiers

**Table 7. Scores by tier and track**, mean over the models of the panel (the keyword script
is left out). *F1*, *task success* and *target score* as in Table 5. *Strict*: every answer
counts, and an answer that cannot be shown scores 0. *Valid-only*: the mean over valid
answers, which shows the difficulty of a tier once the format has been written correctly.

| Tier | Tasks | Structures | F1 (strict) | Task success (strict) | Target score (strict) | Task success, valid-only |
|:---|---:|---:|---:|---:|---:|---:|
| Scene track: Translation | 73 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Scene track: Structure-grounded | 63 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Scene track: Interactions | 40 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Scene track: Name resolution | 39 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Scene track: Clinical variant | 82 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Scene track: Follow-up turn | 58 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Scene track: Several right answers | 26 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Call-list track: Translation | 178 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Call-list track: Structure-grounded | 63 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Call-list track: Clinical variant | 82 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Call-list track: Follow-up turn | 44 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Call-list track: Several right answers | 15 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Call-list track: Viewer settings | 34 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |

### 6.3 The same request in two formats

**Table 8. Paired comparison of the two formats.** For each model, its
258 pairs (one request on both tracks, same target atoms) are split four
ways, twice. A side is *right* when at least two of its three answers are right. *Target-right*
columns (primary): an answer is right when its target score is 1, that is, the requested
atoms are drawn exactly as asked; this is the same test in both formats. *Task success*
columns (secondary): an answer is right when its whole drawn state is exactly right; this is
not the same test in the two formats (Section 3.4). *Both*, *scene only*, *call list only*,
*neither*: the number of pairs right on both sides, on one side only, or on neither. *McNemar
p*: exact test that the two one-sided counts are equal; a small value means that one format
is harder for this model. † marks an optional model.

| Model | Pairs | Target-right: both | Target-right: scene only | Target-right: call list only | Target-right: neither | McNemar p | Task success: both | Task success: scene only | Task success: call list only | Task success: neither | McNemar p |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| claude-haiku-4-5 | 258 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| deepseek-v3.2 | 258 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| … 19 further rows, one per model | | ⟦PENDING: final run⟧ | | | | | | | | | |

Where both formats demand the same knowledge, which is every tier with pairs except the
clinical one, a pair that is target-right on one side only points to the format: the model
knew which atoms were meant and failed to write them in the other format. A pair that is
wrong on both sides is a candidate for an error of content. Clinical pairs must be read
differently. There a right call list does not show that the model knew the residue, because
the viewer can do the mapping (Section 3.4); "call list right, scene wrong" then points to the
mapping, not to the scene format. The counts without the clinical pairs are the cleaner test
of the formats.
⟦PENDING: final run — the same counts without the clinical pairs, and without the 15 pairs in which the call list must switch off part of the default drawing⟧

### 6.4 Clinical variants

**Table 9. Clinical tier on the scene track, by what the request demands.** *Task success* and
*target score* as in Table 5, strict, mean over the models of the panel. *Grounding pack*: the
result of the lookup, including the mapped residue, appended to the request (Table 4). The
rows are two different splits of the same 82 tasks (Section 3.3). *Split A*: would an
answer that copies the number in the variant name as the author residue number be right?
*Split B*: is the target residue numbered as in UniProt? The splits differ in the tasks that
use a traditional name counted along the mature protein. The helix and strand tasks need the
entry's own annotation; they are a subset of the 82 and are also reported apart.

| Clinical tasks (scene track) | Tasks | Task success | Target score | Task success with grounding pack |
|:---|---:|---:|---:|---:|
| **Split A** (primary): the number in the variant name is the author residue number | 34 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| **Split A**: the number in the variant name is **not** the author residue number | 48 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| **Split B**: target residue numbered as in UniProt | 23 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| **Split B**: target residue numbered differently from UniProt | 59 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Helix or strand requested (a subset, reported apart) | 10 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |

This table carries the benchmark's central question. If models read variant numbers at face
value, task success will be high in the first row of Split A and low in the second, and the
grounding pack will close the gap. If models carry out the mapping, the two rows will be
alike.

### 6.5 Follow-up turns, open requests and robustness

**Table 10. Follow-up turns and requests with several right answers.** *Task success*: share
of answers whose drawn state is exactly right (for a request with several right answers: the
drawn state equals any one of the accepted answers), strict, mean over the models of the
panel.

| Group | Scene track: tasks | Scene track: task success | Call-list track: tasks | Call-list track: task success |
|:---|---:|---:|---:|---:|
| Follow-up turns that need a change | 48 | ⟦PENDING: final run⟧ | 36 | ⟦PENDING: final run⟧ |
| Follow-up turns that need no change | 10 | ⟦PENDING: final run⟧ | 8 | ⟦PENDING: final run⟧ |
| Requests with several right answers | 26 | ⟦PENDING: final run⟧ | 15 | ⟦PENDING: final run⟧ |

**Table 11. Planned comparisons.** Each row compares the task success rate (strict, mean over
the models of the panel) between two groups of tasks or two conditions, with a 95% interval on
the difference (structures resampled). *JSON mode*: the provider's option that forces
syntactically valid JSON; that condition has 1 sample per task. *Grounding pack*: as in Table
9. *Format reference*: the reference text for the answer format in the system prompt.

| Comparison | Tasks | Task success, first group | Task success, second group | Difference (95% interval) |
|:---|---:|---:|---:|---:|
| Public split against held-back split (both tracks) | 632 and 165 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Full wording against terse wording | 30 requests (41 tasks) | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Full wording against indirect wording | 30 requests (41 tasks) | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Format reference against format reference plus JSON mode (the 15 models that offer it; 1 sample in JSON mode) | 797 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Format reference against format reference plus grounding pack (name-resolution and clinical tiers, scene track) | 121 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Format reference against no format reference (3 models, scene track) | 381 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |

⟦PENDING: final run — outcome counts per model (valid, invalid JSON, rejected by the viewer, cut off), the repaired scores and the cost per model, as tables in SI Section S8⟧

⟦PENDING: rating study — agreement between people, and between people and the grader's task success, with intervals (Section 5.5)⟧

### 6.6 Preliminary evidence (October 2026 pilot run: older corpus, regraded with the present grader)

<div class="box">

**Everything in this box is preliminary.** It comes from a pilot run of 2026-10-18:
15 models, the scene track only, 70 tasks on
14 structures, 1 answer per task. The tasks were
an earlier corpus; none of them is in the corpus of Section 3. The answers were archived and
are graded here with the present grader (Section 4) against the references of that time, so the
scores differ somewhat from those published in October with the earlier grader. With one
sample and 14 structures, the numbers below can show patterns; they cannot
rank the leading models.

**Finding 1: whether the answer was valid decided the ranking.** Of 1,050 answers,
784 (75%) were valid scenes. Per model the share
ranged from 9% to 99%, and strict F1
from 0.07 to 0.84 (Table P1). The two are nearly the same
ranking: the correlation between a model's share of valid answers and its strict F1 is
r = 0.99. Valid-only, the models are much closer (F1 from
0.78 to 0.95). Of the
266 invalid answers, 227 were not parseable
JSON, and 66% of the 199
whose text was archived opened and closed a different number of braces. A scene is a deeply
nested tree, and one brace too many or too few loses the whole answer. An offline repair of
the JSON turned 183 of those 199 answers into
scene trees (these were not checked by the viewer). This is why the final run reports strict
and valid-only scores side by side and adds a JSON-mode condition.

**Table P1. Pilot run, per model (preliminary).** 70 tasks, one answer each,
ordered by task success. *Valid answers*: answers that parse and that the viewer accepts.
*F1*: how much of the drawn state is right (0 to 1). *Task success*: share of answers whose
drawn state is exactly right. *Strict*: every answer counts, and an answer that cannot be
shown scores 0. *Valid-only*: the mean over valid answers.

| Model | Weights | Valid answers | F1 (strict) | Task success (strict) | F1, valid-only | Task success, valid-only |
|:---|:---|---:|---:|---:|---:|---:|
| gemini-3.5-flash | closed | 66 of 70 | 0.840 | 71.4% | 0.891 | 75.8% |
| llama-4-maverick | open | 57 of 70 | 0.773 | 70.0% | 0.949 | 86.0% |
| deepseek-v4-flash | open | 65 of 70 | 0.798 | 68.6% | 0.860 | 73.9% |
| deepseek-v3.2 | open | 69 of 70 | 0.829 | 65.7% | 0.841 | 66.7% |
| minimax-m3 | open | 63 of 70 | 0.769 | 61.4% | 0.854 | 68.2% |
| claude-haiku-4-5 | closed | 67 of 70 | 0.799 | 60.0% | 0.835 | 62.7% |
| glm-5.2 | open | 63 of 70 | 0.761 | 58.6% | 0.846 | 65.1% |
| kimi-k2.6 | open | 51 of 70 | 0.620 | 50.0% | 0.851 | 68.6% |
| gemma-3-27b-it | open | 57 of 70 | 0.639 | 48.6% | 0.785 | 59.7% |
| qwen3-next-80b-a3b-instruct | open | 64 of 70 | 0.714 | 45.7% | 0.781 | 50.0% |
| gpt-5.4-nano | closed | 53 of 70 | 0.615 | 44.3% | 0.812 | 58.5% |
| qwen3-30b-a3b-instruct-2507 | open | 39 of 70 | 0.502 | 40.0% | 0.901 | 71.8% |
| gpt-oss-120b | open | 44 of 70 | 0.533 | 38.6% | 0.849 | 61.4% |
| gpt-oss-20b | open | 20 of 70 | 0.224 | 20.0% | 0.785 | 70.0% |
| nemotron-3-super-120b-a12b | open | 6 of 70 | 0.070 | 5.7% | 0.822 | 66.7% |

**Finding 2: clinical tasks lost their points on unrequested context, not on the residue.**
The clinical tier scored lowest: strict F1 0.31, and task success
3.7%, that is 5 of
135 answers (Table P2, Figure 6). The natural reading is that finding the
residue of a variant is hard. That reading is wrong for this run. In
87 of the 135 answers, which is
91% of the 96 valid ones,
the requested residue was drawn exactly as in the reference: same atoms, same representation,
same colour. The points were lost elsewhere. Each clinical reference of that corpus also drew
a grey cartoon of the whole protein, and the requests asked only for the residue. An answer
that drew the residue alone was missing a fact; an answer that drew the cartoon differently had
a wrong one. There was a second flaw: all 9 clinical tasks
used 1 structure, in which author numbers equal UniProt
numbers. The residue could be found without any mapping, so the tier could not test the
mapping at all.

**Table P2. Pilot run by tier, all models pooled (preliminary).** *Answers*: one per model and
task. *Valid*: answers that parse and that the viewer accepts. *F1, earlier grader*: the score
under the grader used in October, for comparison. *F1* and *task success*: as in Table P1,
strict. *Requested part exactly right*: among answers to tasks whose reference marks out a
requested part against a background, the share that draw that part with exactly the
reference's atoms, representation and colour (strict). It is the forerunner of the target
score of Section 4.2: the pilot tasks stored no target atoms, so the requested part is taken
from the reference. The October corpus had too few tasks in three of its tiers to show them
apart, so they are pooled in one row.

| Tier (October corpus) | Answers | Valid | F1, earlier grader | F1 | Task success | Requested part exactly right |
|:---|---:|---:|---:|---:|---:|---:|
| Translation | 615 | 491 | 0.780 | 0.773 | 69.9% | 80.0% of 105 |
| Structure-grounded, name resolution and interactions | 300 | 197 | 0.546 | 0.488 | 29.7% | 45.6% of 195 |
| Clinical variant | 135 | 96 | 0.483 | 0.314 | 3.7% | 64.4% of 135 |
| **All** | 1050 | 784 | 0.675 | 0.632 | 49.9% | |

![**Figure 6. Pilot run: three scores by tier (preliminary).** Strict means over all answers of all 15 models. *F1*: how much of the drawn state is right. *Task success*: drawn state exactly right. *Requested part exactly right*: the residues or ligand the request is about drawn exactly as in the reference, whatever the rest of the answer shows; it is the forerunner of the target score. Three tiers with few tasks are pooled in the middle group. In the clinical tier the requested part was usually right and the whole drawn state almost never.](generated/fig_october_regrade.svg)

**How Finding 2 changed the design.** (i) A reference now holds only what the request
states; if context is wanted, the request asks for it in words. (ii) Every task stores its
target atoms, and the target score is reported next to F1 and task success, so that context
and substance can no longer be confused. (iii) An attribute that the request does not state is
free (Section 3.5). (iv) The clinical tier was rebuilt: 82 tasks on
25 proteins, 59 of them with a numbering offset, in place of
9 tasks on one protein with none.

**Finding 3: grounding packs did not help.** Appending each task's grounding pack to the
request lowered task success over all tasks from 49.9% to
46.3%, and the number of valid answers from 784 to
739: the longer prompt produced more invalid answers. On the clinical
tier, task success was 3.7% without the pack and
3.0% with it. Finding 2 explains why the pack had little
to add: the residue was already right without it. Whether a pack helps when it holds a number
that the model cannot guess is a question for the rebuilt clinical tier (Table 9).

**Finding 4: without the format reference, no answer was valid.**
The condition with the instruction and the rule for the answer only was run on 3
models, with and without grounding packs. None of their 420 answers was a
valid scene. For these models, knowledge of the
MolViewSpec format came from the prompt and not from training.

**Finding 5: our first call-list track did not separate models from a keyword script.** That
track had 20 hand-written tasks and a grader that compared call lists field
by field. Under that grader the keyword script reached a mean F1 of
0.72, and the 16 models between
0.72 and 0.95 (run of 2026-07-04). These numbers are the reason the track
was rebuilt; they are not results of the present benchmark.

**Finding 6: the pilot rating study was too small to validate anything.** *What was done.* In
October, each valid scene that scored below 1 was rendered, and an image judge (Section 5.5)
was shown its picture beside the picture of the reference. Volunteers then judged a sample of
the same picture comparisons. 3 raters, one of them an author, gave
114 verdicts of "same" or "different" on 109 picture
comparisons.

*Result.* People and the image judge gave the same verdict in 79% of
cases. Cohen's kappa, which is agreement beyond what chance would give (0 is chance, 1 is
perfect), was 0.54 (95% interval 0.34 to
0.71). Where the judge had said "same", people agreed in
74% of cases (57% to
89%), or in 62% (40%
to 85%) when the author's verdicts are left out.

*Limits.* Only 1 of the 3 raters met the
attention-check rule that was written before the data were seen (at least
80% right on each kind of check item): the author was never shown a check
item, and one volunteer answered "can't tell" on a check, which the rule counts as a miss. The
numbers above include all raters and so depart from that rule. Only
5 picture comparisons received two verdicts, so agreement between
people cannot be estimated. The pilot does not validate the image judge, and it supports no
statement about tiers, single models or the final run. No score in this paper uses the image
judge: under the earlier grader, counting the judge's "same" verdicts as right changed no
model's mean F1 by more than 0.028.

*End of the preliminary evidence.*

</div>

## 7. What we got wrong and changed

The benchmark of Section 3 is the second version of most of its parts. We list what the first
version got wrong, how we found out, and what replaced it, because each error is one that
another benchmark of this kind could make.

1. **References drew more than the request asked.** Our clinical references contained
   unrequested context, and we read the resulting low score as a difficulty of the lookup
   (Section 6.6, Finding 2, tells this in full). *Change*: a reference contains only what the
   request states, and the target score is reported with every result.
2. **The clinical tier could not test what it was for.** It had
   9 tasks on one protein whose structure is numbered as
   UniProt is. *Change*: 82 tasks on 25 proteins and
   31 structures; 59 targets have an offset (their author
   number differs from their UniProt number), and results are split by whether the number in
   the variant name is the author number.
3. **"Pathogenic" was taken from a secondary source.** We first took variants that UniProt
   lists as pathogenic. ClinVar's aggregate classification disagreed for
   20% of them, and some variants named in our earlier tasks are now
   classified as conflicting. *Change*: every variant is confirmed against ClinVar's own
   record, and the dates are stored (Section 3.1).
4. **The graders compared text.** The first scene grader compared scene trees path by path. It
   failed 264 of 630 correct control
   answers that were merely written differently. The first call-list grader compared call
   sequences. It passed 75 of 420
   wrong control answers and failed 311 of
   575 correct ones, and a keyword script scored close to the
   models (Section 6.6, Finding 5). *Change*: both tracks are graded on drawn state, and the
   control set is run as a test on every change.
5. **Hand-written call-list tasks had errors.** A check of those references against the
   structures found label numbers where author numbers were meant, and one task was the worked
   example of the prompt. *Change*: every reference is generated, replayed in the real viewer
   for a sample, and the prompt's example structure is excluded from the corpus.
6. **Some requests had no single answer.** An early request to highlight "all pathogenic
   residues" of one protein resolved to 204 residues, which no user means. "Show me lysozyme"
   was graded against one arbitrary view. *Change*: clinical requests name each variant;
   requests with a countable ambiguity have their own tier with every accepted answer listed;
   open-ended requests are left out (Section 9).
7. **Raters could not see what they were rating.** In the pilot rating study, a single
   highlighted residue on a whole complex was a few pixels wide; a volunteer flagged the
   reference as wrong when it was only unreadable. A volunteer also found references in which
   two cartoons overlapped. *Change*: pictures are framed on the target atoms from one shared
   camera; overlapping references were corrected; the next study completes two ratings of a
   picture comparison before opening new ones.
8. **One answer per task, few structures, a short limit on answer length.** The pilot drew
   one answer per task on 14 structures, with a limit of 2,000 tokens and no
   record of how often an answer was cut off. *Change*: 3 answers per task, 78
   structures, a limit of 8,000 tokens, and the finish reason archived for
   every call.
9. **The prompts taught answers that the graders marked wrong.** Before the final run, the
   benchmark was reviewed four times by language-model reviewers, each given one role
   (structural biologist, clinical geneticist, benchmark methodologist, tester of the grader).
   The reviewers wrote natural answers by hand and graded them, and we reproduced each
   finding before acting on it. The worked example of the scene prompt selected a named
   compound in a way the references did not; the worked example of the call-list prompt
   coloured a residue in a form that many generated tasks did not accept; a residue named by
   UniProt number on a predicted model was scored as selecting nothing; and a scene with an
   unreadable file passed. The same reviews found clinical requests whose "pathogenic" record
   belonged to another gene or to a pair of variants (Section 3.1). *Change*: each finding was
   fixed in the generator or grader and is now covered by an automated test and by a new kind
   of control answer, and both prompt examples are graded by the benchmark's own grader as a
   test.

## 8. Discussion

⟦PENDING: final run — discussion of the results: which tiers separate models, what the paired comparison shows, whether the held-back split differs from the public one⟧

Three points can be made before the final run, because they concern the instrument and not
the models.

**Exactness is measurable for this task.** A viewer scene has a definite content: these atoms,
drawn this way. Once references are computed from the structure and answers are resolved to
atoms, "is it right?" has a yes-or-no answer that needs no judge model and no rubric. On the
control set that answer is stable under rewriting (2,105 controls, no error, on a
grader developed against them), and graders that compare text are not: they failed
42% and 54% of
correct control answers.

**One score is not enough.** The pilot run gave three different pictures of the same answers.
Strict scores mostly measured whether a model can close its braces. F1 on the clinical tier
mostly measured whether a model reproduced a background. Only a score restricted to the
requested atoms showed that the residue was usually right. We therefore report the task
success rate as the primary score, the target score beside it to separate substance from
unrequested context, F1 for partial credit, and each of them strict and valid-only.

**A benchmark's references need the same scrutiny as the models.** The most important
finding so far concerns our own references (Section 7). It was found by asking where valid
answers lost their points, and not by looking at totals. We recommend that analysis to anyone
who builds a benchmark with partial credit.

## 9. Limitations

Four limits bound the claims of this paper more than the others: each track is graded by the
rules of one viewer; the requests come from templates; the tasks are public; and the grader
has been tested only against cases that we foresaw. The full list follows in four groups.

### Scope

- **One viewer per track.** The scene track is graded by the rules of Mol\* 5.9.0, and the
  call-list track by those of PDBe Mol\* 3.3.2. MolViewSpec is designed to be independent of the
  viewer, but Mol\* is its implementation in practice. We make no claim about PyMOL, ChimeraX
  or VMD.
- **Closed-book, one answer.** A model cannot look anything up, ask back, or see the picture.
  A product that wraps a model in tools, validation and retries may do better. We measure the
  model, not such a product.
- **No open-ended tasks.** Requests such as "show the active site clearly" have no single
  right drawn state and are not in the corpus. Requests with a countable ambiguity are, in a
  small tier.

### Corpus

- **Generated requests.** Requests come from templates. They are cleaner than what people
  type, and they have been read for naturalness by the authors and by the reviewers of the
  corpus (Section 7), not yet by an independent structural biologist. The terse and indirect
  phrasings were written out one by one by the language-model coding assistant used in this
  work, and checked by rule for dropped values; no person has read them all.
- **Public tasks and contamination.** Earlier MolBench tasks have been public since May 2026,
  and the public split of this corpus will be public when the paper is. A model trained later
  may have seen them. The held-back split does not solve this. Its tasks were in a public
  repository for some days before the run, and nearly all tasks in both splits are new, so it
  compares structures that earlier MolBench tasks had used with structures that none had used,
  not seen tasks with unseen tasks (Section 3.6). Three of its structures share a protein with
  a public structure. It cannot show that a model has, or has not, memorised tasks, and it
  cannot protect future runs. The generators are seeded, so a fresh split on new structures
  can be drawn.
- **A panel of 79 structures.** The structures were chosen by hand for coverage and
  are mostly well known: the median year of deposition is 1999, and only
  10 entries date from 2020 or later. Scores on them may be higher
  than on a recent entry that a model has never read about. All but
  2 entries have at most 15,000 atoms, so large
  assemblies are not tested.
- **Clinical labels move.** ClinVar classifications change as evidence is submitted. Ours are
  a snapshot of 2026-11-12 to 2026-11-16. For
  20% of the candidates, ClinVar's classification already differed
  from the label we started from (Section 3.1). Several of the variants we use, including the
  running example, rest on records whose review status is "criteria provided, single submitter". The
  benchmark uses a variant only as an address: which residue does this name point to? That
  address does not depend on the classification. No task asks for a judgement about disease.
- **The format gap in the clinical pairs.** On the call-list track the viewer can map a UniProt
  position itself; on the scene track the model must. The paired comparison is therefore
  reported with and without clinical pairs. The two system prompts also differ in length,
  because the two format references do, and in the pilot run a longer prompt lowered the share
  of valid answers. A difference between the tracks can therefore come from the prompt as well
  as from the format.

### Grader

- **Tested only against cases we foresaw.** The grader makes no error on the control set
  because it was corrected until it made none (Section 4.5). How often it misjudges a way of
  writing an answer that the control set lacks is not known. The human check of the grader has
  so far been run only as a pilot with 3 raters (Section 6.6). Until the
  planned study is done, the evidence that task success matches what people see is the control
  set and the read-back from the viewers.
- **Name resolution: text comparison outside the panel.** A request that names a protein
  accepts any PDB entry of it. Only panel entries have frozen atom tables, so on any other
  accepted entry an answer's selections are compared with the reference's as text. The common
  ways of writing "the protein" pass; a correct selection by chain identifier does not. The
  tier's results are reported apart for answers on the reference entry and on any other
  accepted entry.
- **Partial credit is a choice.** Facts have equal weight, and a wrong colour counts half.
  Other choices would give other F1 values. Task success does not depend on them.
- **What the grader does not model.** Atoms are compared on the deposited model; single copies
  in a symmetry-built assembly are not modelled. Label styling, sizes and camera numbers are
  not graded. Views of the call-list viewer that need live services (superposition, ligand
  view, annotations, density maps) are graded as declared settings; the atoms they would draw
  are not modelled. SI Section S4.8 gives the full list, including four call-list actions that
  one host of the viewer ignores.

### Run

- **What the run can and cannot detect.** Track totals and tier means rest on dozens to nearly
  two hundred tasks and are estimated with useful precision. Several planned contrasts are
  descriptive only: the public against the held-back split within one tier (held-back tasks
  sit on 15 structures); the 10 helix and strand
  tasks; paraphrases within one tier (30 requests in all); and
  the matched clinical tasks. Of the last there are 8 sets that ask the
  same variant on a structure with and on one without an offset, on
  4 proteins, and the structure without an offset is always a
  predicted model, so "no offset" and "predicted model" cannot be told apart. We report these
  contrasts with intervals and do not test them.
- **The floor.** The keyword script is a weak floor. A script of regular expressions over the
  request templates, with no knowledge of any structure, would solve a share of the
  translation tier, and on the clinical tier the number in the variant name is the right
  author number in 34 of the 82 tasks (Section 3.3). Clinical
  results are therefore split by that property, and follow-up results by whether the right
  answer is to change nothing.
- **Prices and hosted models change.** Costs are list prices on the day of the run. Hosted
  models are updated and withdrawn; the archived answers are the lasting record.

## 10. Conclusion

MolBench shows that control of a molecular viewer by a language model can be graded exactly
and without a judge model. References are computed by script from the structure, the SIFTS
mapping and ClinVar, and answers are compared on the atoms, representations and colours that
a viewer would draw. Three things hold before any final result. Graders that compare text
failed 42% and
54% of the correct control answers that the drawn-state
grader accepts. One score is not enough: we report the task success rate, the target score
and F1, each strict and valid-only. And in the pilot run the largest source of error was our
own references, which drew more than the requests asked for.
⟦PENDING: final run — two sentences on the results: how well the models control the viewer on each track, and what the paired comparison shows⟧

## 11. Ethics, people and licences

**No patient data.** The benchmark contains no data about individuals. Clinical variants come
from ClinVar's public variant-level records; no individual-level data are used. A variant
serves only as a residue position with a classification label.

**Not for clinical use.** A high score does not make a model fit to interpret variants. The
clinical tier measures whether a model can locate a residue in a structure. The data providers
say the same of their data: UniProt and the AlphaFold Protein Structure Database state that
their content is not a substitute for professional medical advice.

**Volunteer raters.** The rating study asks volunteers to compare two pictures of a molecule
at a time. It collects their answers, optional free-text notes
and the time taken per item. Raters are identified in the analysis by pseudonyms; no names,
contact details or rater identifiers are published. ⟦PENDING: Dan — confirm the consent wording shown to raters, and whether the target journal or the author's institution requires an ethics statement or a waiver for this study⟧

**Use of language models in this work.** Language models are the subject of the study. They
were also used as coding and drafting assistants in building the benchmark and in writing
this manuscript. The authors checked all content and are responsible for it.
⟦PENDING: Dan — final wording of this disclosure, which the journal asks for in the Acknowledgements⟧

**Licences of data and software.** We read each licence at its source on 2026-11-16 (Table
12). Frozen copies of third-party data in the repository keep their original terms and are
attributed in the repository.

**Table 12. Data and software used, with licence or terms as stated at the source.**

| Resource | Used for | Licence or terms | Read at |
|:---|:---|:---|:---|
| Protein Data Bank archive and RCSB PDB web services [24] | structure files, atom tables, entry annotations | CC0 1.0 public-domain dedication | rcsb.org/pages/usage-policy |
| PDBe: SIFTS mapping, updated structure files, search of entries per protein [8, 28] | residue mapping, choice of structures | EMBL-EBI terms of use: no additional restrictions on use or redistribution; attribution expected | ebi.ac.uk/about/terms-of-use |
| UniProt [7] | sequences, candidate variants | CC BY 4.0 | uniprot.org/help/license |
| ClinVar [6] | classification of variants | NCBI molecular data policy: NCBI places no restrictions on use or distribution; submitters may hold rights | ncbi.nlm.nih.gov/home/about/policies |
| AlphaFold Protein Structure Database [25, 26] | 5 predicted models | CC BY 4.0 | alphafold.ebi.ac.uk (licence and disclaimer) |
| Mol\* [16] and MolViewSpec [20] | scene format, validation, read-back, pictures | MIT | github.com/molstar |
| PDBe Mol\* [22] | viewer of the call-list track | Apache-2.0 | github.com/molstar/pdbe-molstar |
| ipymolstar [23] | Python host of that viewer | MIT | pypi.org/project/ipymolstar |
| GEMMI [29] | reading structure files | MPL-2.0 | github.com/project-gemmi/gemmi |
| json-repair [32] | repair counterfactual | MIT | github.com/mangiucugna/json_repair |

MolBench's own code, tasks and references are released under the MIT licence.

## 12. Data and code availability

- **Code, tasks, references, graders, control set:** <https://github.com/dbolser/MolBench>
  (MIT licence). ⟦PENDING: corpus freeze — version tag and hash of the frozen corpus⟧
- **Archive:** ⟦PENDING: deposit — DOI of the frozen corpus, including the held-back split, and of the raw model answers and score files of the final run⟧
- **Rating data:** ⟦PENDING: deposit — anonymised ratings of both rating studies, with the analysis scripts⟧
- **Results browser:** <https://dbolser.github.io/MolBench/>.
- **This paper:** every table, figure and number in this paper is regenerated by scripts in
  the repository from the task files, the frozen data and the archived answers; the
  repository's notes on the paper say how.

Grading needs no network access and no paid service. Validation by the viewer and the pictures
for the rating study need a browser without a display and the Mol\* bundle, both free.

## Supporting Information

The Supporting Information (one PDF file) contains: the running example in full (Section S1);
all task templates with an example request each (S2); the structure panel and how it was
chosen (S3); the full grading rules and the known limits of the grader (S4); the control set
by kind (S5); the run manifest, the models and their prices (S6); the system prompts (S7); and
further tables of the pilot run (S8).

## Author information

⟦PENDING: Dan — corresponding author, author contributions, and the notes the journal asks for (competing interests)⟧

## Acknowledgements

⟦PENDING: Dan — acknowledgements, funding, and the disclosure of language-model use⟧

## References

1. Goddard T. Claude Chat to operate ChimeraX. *UCSF RBVI web page, 4 December 2025* 2025. <https://www.rbvi.ucsf.edu/chimerax/data/claude-dec2025/claude_mcp.html>
2. Mol* developers. Prism viewer (pull request 1978) and v6: PyMOL and VMD commands (pull request 2052), molstar/molstar. *Source-code pull requests, merged 2026-10-16 and 2026-10-25* 2026. <https://github.com/molstar/molstar/pull/1978>
3. Navarro C, Torrens-Fontanals M, Thölke P, Doerr S, De Fabritiis G. Speak to a Protein: An Interactive Multimodal Co-Scientist for Protein Analysis. *Journal of Chemical Information and Modeling* 2026;66(19):12391–12401. Preprint: arXiv:2510.17826. doi:[10.1021/acs.jcim.6c01738](https://doi.org/10.1021/acs.jcim.6c01738)
4. Sun J, Li A, Deng Y, Li J. ChatMol Copilot: An Agent for Molecular Modeling and Computation Powered by LLMs. *Proceedings of the 1st Workshop on Language + Molecules (L+M 2024)* 2024:55–65. doi:[10.18653/v1/2024.langmol-1.7](https://doi.org/10.18653/v1/2024.langmol-1.7)
5. Faezov B, Dunbrack RL. PDBrenum: A webserver and program providing Protein Data Bank files renumbered according to their UniProt sequences. *PLOS ONE* 2021;16(7):e0253411. doi:[10.1371/journal.pone.0253411](https://doi.org/10.1371/journal.pone.0253411)
6. Landrum MJ, Lee JM, Benson M, Brown GR, Chao C, Chitipiralla S, Gu B, Hart J et al. ClinVar: improving access to variant interpretations and supporting evidence. *Nucleic Acids Research* 2018;46(D1):D1062–D1067. doi:[10.1093/nar/gkx1153](https://doi.org/10.1093/nar/gkx1153)
7. The UniProt Consortium. UniProt: the Universal Protein Knowledgebase in 2025. *Nucleic Acids Research* 2025;53(D1):D609–D617. doi:[10.1093/nar/gkae1010](https://doi.org/10.1093/nar/gkae1010)
8. Dana JM, Gutmanas A, Tyagi N, Qi G, O'Donovan C, Martin M, Velankar S. SIFTS: updated Structure Integration with Function, Taxonomy and Sequences resource allows 40-fold increase in coverage of structure-based annotations for proteins. *Nucleic Acids Research* 2019;47(D1):D482–D489. doi:[10.1093/nar/gky1114](https://doi.org/10.1093/nar/gky1114)
9. Sun Q, Liu Z, Ma C, Ding Z, Xu F, Yin Z, Zhao H, Wu Z et al. ScienceBoard: Evaluating Multimodal Autonomous Agents in Realistic Scientific Workflows. *arXiv preprint* 2025. v3 is marked “ICLR 2026 Camera Ready Version”. arXiv:[2505.19897](https://arxiv.org/abs/2505.19897) <https://arxiv.org/abs/2505.19897>
10. Goddard TD, Huang CC, Meng EC, Pettersen EF, Couch GS, Morris JH, Ferrin TE. UCSF ChimeraX: Meeting modern challenges in visualization and analysis. *Protein Science* 2018;27(1):14–25. doi:[10.1002/pro.3235](https://doi.org/10.1002/pro.3235)
11. Ai K, Miao H, Tang K, Gorski N, Sun J, Liu G, Ingolfsson HI, Lenz D et al. SciVisAgentBench: A Benchmark for Evaluating Scientific Data Analysis and Visualization Agents. *arXiv preprint* 2026. arXiv comment: IEEE Transactions on Visualization and Computer Graphics (IEEE VIS '26). arXiv:[2603.29139](https://arxiv.org/abs/2603.29139) <https://arxiv.org/abs/2603.29139>
12. Dai D, Qi H, Liu L, Li Y, Chen B, Dou Z, Zeng Q, Kang Q et al. OSWorld-Science: A Benchmark of Computer Use Agents for Learning and Using Scientific Software. *arXiv preprint* 2026. arXiv:[2609.39903](https://arxiv.org/abs/2609.39903) <https://arxiv.org/abs/2609.39903>
13. Xie T, Zhang D, Chen J, Li X, Zhao S, Cao R, Toh JH, Cheng Z et al. OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments. *arXiv preprint* 2024. arXiv:[2404.07972](https://arxiv.org/abs/2404.07972) <https://arxiv.org/abs/2404.07972>
14. Qin Y, Liang S, Ye Y, Zhu K, Yan L, Lu Y, Lin Y, Cong X et al. ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs. *arXiv preprint* 2023. arXiv:[2307.16789](https://arxiv.org/abs/2307.16789) <https://arxiv.org/abs/2307.16789>
15. Yao S, Shinn N, Razavi P, Narasimhan K. tau-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains. *arXiv preprint* 2024. arXiv:[2406.12045](https://arxiv.org/abs/2406.12045) <https://arxiv.org/abs/2406.12045>
16. Sehnal D, Bittrich S, Deshpande M, Svobodová R, Berka K, Bazgier V, Velankar S, Burley SK et al. Mol* Viewer: modern web app for 3D visualization and analysis of large biomolecular structures. *Nucleic Acids Research* 2021;49(W1):W431–W437. doi:[10.1093/nar/gkab314](https://doi.org/10.1093/nar/gkab314)
17. Jia D, Irger A, Besançon L, Strnad O, Luo D, Björklund J, Kouyoumdjian A, Ynnerman A et al. VOICE: Visual Oracle for Interaction, Conversation, and Explanation. *IEEE Transactions on Visualization and Computer Graphics* 2025;31(10):8828–8845. Preprint: arXiv:2304.04083. doi:[10.1109/TVCG.2025.3579956](https://doi.org/10.1109/TVCG.2025.3579956)
18. Cortes Rodriguez F, Abriata L. Speech recognition assisted by large language models to command software orally -- Application to an augmented and virtual reality web app for immersive molecular graphics. *arXiv preprint* 2026. arXiv:[2603.02901](https://arxiv.org/abs/2603.02901) <https://arxiv.org/abs/2603.02901>
19. RenhaoL. molstar-mcp: a Model Context Protocol server that builds MolViewSpec scenes for Mol*. *Software, MIT; repository created 2026-05-31* 2026. <https://github.com/RenhaoL/molstar-mcp>
20. Midlik A, Bittrich S, Fleming JR, Nair S, Velankar S, Burley SK, Young JY, Vallat B et al. MolViewSpec: a Mol* extension for describing and sharing molecular visualizations. *Nucleic Acids Research* 2025;53(W1):W408–W414. doi:[10.1093/nar/gkaf370](https://doi.org/10.1093/nar/gkaf370)
21. Bittrich S, Midlik A, Varadi M, Velankar S, Burley SK, Young JY, Sehnal D, Vallat B. Describing and Sharing Molecular Visualizations Using the MolViewSpec Toolkit. *Current Protocols* 2024;4(7):e1099. doi:[10.1002/cpz1.1099](https://doi.org/10.1002/cpz1.1099)
22. PDBe. PDBe Molstar (pdbe-molstar): the PDBe implementation of Mol*, version 3.3.2. *Software, Apache-2.0; version 3.3.2 published on npm 2024-11-25* 2024. <https://github.com/molstar/pdbe-molstar>
23. Smit J, ipymolstar contributors. ipymolstar: Mol* as an anywidget, version 0.1.0. *Software, MIT; version 0.1.0 released on PyPI 2025-04-10* 2025. <https://github.com/molstar/ipymolstar>
24. wwPDB consortium. Protein Data Bank: the single global archive for 3D macromolecular structure data. *Nucleic Acids Research* 2019;47(D1):D520–D528. doi:[10.1093/nar/gky949](https://doi.org/10.1093/nar/gky949)
25. Varadi M, Bertoni D, Magana P, Paramval U, Pidruchna I, Radhakrishnan M, Tsenkov M, Nair S et al. AlphaFold Protein Structure Database in 2024: providing structure coverage for over 214 million protein sequences. *Nucleic Acids Research* 2024;52(D1):D368–D375. doi:[10.1093/nar/gkad1011](https://doi.org/10.1093/nar/gkad1011)
26. Jumper J, Evans R, Pritzel A, Green T, Figurnov M, Ronneberger O, Tunyasuvunakool K, Bates R et al. Highly accurate protein structure prediction with AlphaFold. *Nature* 2021;596(7873):583–589. doi:[10.1038/s41586-021-03819-2](https://doi.org/10.1038/s41586-021-03819-2)
27. PDBe-KB consortium. PDBe-KB: a community-driven resource for structural and functional annotations. *Nucleic Acids Research* 2020;48(D1):D344–D353. doi:[10.1093/nar/gkz853](https://doi.org/10.1093/nar/gkz853)
28. PDBe-KB consortium. PDBe-KB: collaboratively defining the biological context of structural data. *Nucleic Acids Research* 2022;50(D1):D534–D542. doi:[10.1093/nar/gkab988](https://doi.org/10.1093/nar/gkab988)
29. Wojdyr M. GEMMI: A library for structural biology. *Journal of Open Source Software* 2022;7(73):4200. doi:[10.21105/joss.04200](https://doi.org/10.21105/joss.04200)
30. Vollmar M, Westrip S, Nair S, Balasubramaniyan B, Velankar S, Jones L, Strickland P. Associating protein residues in the literature with structural data. *Acta Crystallographica Section D Structural Biology* 2026;82(2):113–125. doi:[10.1107/S2059798326000021](https://doi.org/10.1107/S2059798326000021)
31. Li Z, Kong X, Su J, Ma Z, Li M, Li S, Zhang Y, Rong Y et al. From Macro to Micro: Benchmarking Microscopic Spatial Intelligence on Molecules via Vision-Language Models. *arXiv preprint* 2025. arXiv:[2512.10867](https://arxiv.org/abs/2512.10867) <https://arxiv.org/abs/2512.10867>
32. Baccianella S. json_repair: repair malformed JSON from LLMs, APIs, logs, and user input in Python. *Software, MIT* 2026. <https://github.com/mangiucugna/json_repair>
33. Efron B. Bootstrap Methods: Another Look at the Jackknife. *The Annals of Statistics* 1979;7(1):1–26. doi:[10.1214/aos/1176344552](https://doi.org/10.1214/aos/1176344552)
34. McNemar Q. Note on the Sampling Error of the Difference Between Correlated Proportions or Percentages. *Psychometrika* 1947;12(2):153–157. doi:[10.1007/BF02295996](https://doi.org/10.1007/BF02295996)
