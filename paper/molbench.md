<!-- Built by paper/build.py from paper/sections/ and paper/generated/*.json (run numbers: October 2026 panel, PRELIMINARY). Do not edit: edit the sources. -->

# MolBench: Grading Language Models on What a Molecular Viewer Would Show

⟦PENDING: Dan — author list, affiliations, corresponding author⟧

*Draft for review. Every number in this paper is written by a script from the task files, the
frozen data or archived model answers; none is typed by hand. A cell or sentence marked
PENDING in double brackets waits for the final run or for an author decision. The
results that exist today come from the first version of the benchmark, chiefly from a pilot
run in October 2026. They are reported in the boxed Section 6.6 and are called pilot results
wherever another section cites them.*

⟦PENDING: Dan — graphic for the table of contents, which the journal asks for⟧

## Abstract

Language models now drive molecular viewers, and a wrong picture looks as polished as a
right one. MolBench grades by rule, without a judge model, what the Mol\* viewer would draw:
which atoms, which representation, which colour. The model sees only the request and a format
guide: no structure file, no lookup. Scripts compute references from structure files, a
residue-numbering table (SIFTS) and a clinical variant archive (ClinVar). The
797 tasks on 78 structures form eight categories. One
asks about variants that ClinVar classifies as pathogenic or likely pathogenic. The variant's
name usually gives its UniProt sequence position; the structure often numbers that residue
differently. Do models convert the number, or copy it? To separate content from format
errors, 258 requests are posed twice: as a MolViewSpec scene and as
PDBe Mol\* viewer calls. The grader agrees with all 2,175 control answers used to
develop it. In a pilot, clinical tasks scored lowest although most answers drew the right
residue. Our references drew an unrequested cartoon (a ribbon), and all clinical tasks used
one structure numbered as its UniProt sequence, which needs no conversion. Both are
corrected, and a target score now grades the requested atoms and ignores background.
⟦PENDING: final run — main results on both tracks and the paired comparison, with the number of models, in two sentences, which replace the four sentences on the pilot run so that the abstract stays within its limit⟧

## 1. Introduction

Molecular viewers are how structural biologists look at their data, and they are hard to
drive. The data are *structures*: the three-dimensional atom coordinates of molecules. Each
structure deposited in the Protein Data Bank (PDB) is an *entry* with a four-character
identifier, such as 2NWD. To show one residue of one chain (one amino acid of one protein molecule in the file), a
user must know how the viewer writes a selection, the chain identifier, and which of several
residue numbering schemes applies. Language models
promise to remove that barrier: the user says what they want, and the model writes the
commands. Several viewers now ship such assistants, or can be operated by one through a
programming interface [1–4].

Whether these assistants are right is rarely measured, and a wrong answer is hard to see. One
request, which we follow through this paper and always quote as it is in the task file, shows
why:

> *"PDB entry 2NWD: the LYZ (Lysozyme C, UniProt P61626) variant p.W82R is classified as pathogenic in ClinVar. Show the residue it replaces as yellow spacefill spheres."*

The request asks for "the residue it replaces": the tryptophan (W) that the variant
p.W82R turns into an arginine (R). A model that takes the
82 of that name as the residue number selects residue
82 of the file. That residue is a serine. The model returns a clean
picture of the wrong amino acid, and nothing in the picture says so. The tryptophan is residue
64 of this file.

The two numbers come from two ways of counting. The position 82 is
counted along the sequence of human lysozyme in UniProt, the reference database of protein
sequences (the prefix "p." marks a description of a change in a protein). That sequence
begins with the 18-residue signal peptide, a leading segment that the cell cuts off after the protein
is made. Entry 2NWD numbers the same chain from the first residue of the mature protein, the protein that is left
once that segment has been cut off; older papers accordingly call the variant
W64R. The case is not unusual: a survey of the PDB found that 38.6% of 176,507
entries contain proteins that are not numbered as their UniProt sequences are
[5]. The request also states a classification. It comes from ClinVar, a public archive of human
genetic variants and their clinical classification. The benchmark uses the variant only as an
address: which residue does the name point to? It never asks whether a variant causes disease
(Section 9.2; Section 3.2 gives the ClinVar record of this variant).

**What the model is given.** In MolBench the model receives only the request and a guide to
the answer format. It does not see the structure file, it cannot look anything up, and it
does not see the picture that its answer produces. To answer the request above it must
therefore know, from its training, that entry 2NWD is numbered from the mature
protein. This is the hardest way to ask the question, and it is the way a model is used when
it has no tools (a *bare* model).

**Thesis.** Whether a language model has driven a molecular viewer correctly can be decided
by rule, without a second model as judge, if two conditions hold: each reference answer is
computed from the structure itself, and each answer is graded on what the viewer would draw,
not on how the answer is written.

MolBench is a benchmark built on this thesis (Figure 1). The reference for the request above
is not written by a person. A script reads the variant from ClinVar [6],
maps its UniProt position [7] to the residues of the entry with the SIFTS mapping
[8], a public table that gives, for each residue of a PDB entry, its position in
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

![**Figure 1. From public data to a score.** Steps 1 to 6 are numbered, in two rows: frozen public data are turned into tasks by generator scripts; each model is given a guide to the answer format and the request, and answers each task three times, independently; the grader resolves the reference and the answer to their drawn state and compares them. Below the steps: the four checks that involve no model (Section 3.7). A *pair* is one request posed on both tracks. *Set-aside structures*: 15 structures that no earlier release of the benchmark used; their tasks are public too (Section 3.6). *F1*: how much of the drawn state is right, with partial credit. *Task success*: the drawn state is exactly right. *Target score*: how far the requested style is on the requested atoms and on no others (0 to 1); unrequested background, such as a cartoon of the protein, is ignored. *Strict* and *valid-only* are two ways to average a score (Section 4.4).](generated/fig_pipeline.svg)

This paper makes four contributions, presented in this order.

1. **A corpus built by script** (Section 3). It has 797 tasks on
   78 structures in eight categories of task: four differ in what the
   model must know beyond the request, and four in the form of the task (Section 3.3). They
   include 82 clinical-variant requests on
   25 proteins; in 48 of them a model that copies
   the number from the variant name selects the wrong residue (Section 3.3.1). Every reference
   records how it was made and is tested against the structure.
2. **A grader on drawn state, tested against a control set** (Section 4). It gives three
   scores with plain definitions, and it is tested on 2,175 control answers whose
   verdict is known from how they were made.
3. **A paired design** (Sections 3.4 and 5). The benchmark has two halves, which we call
   *tracks*. On the *scene track* an answer is a MolViewSpec scene, a description of what the
   Mol\* viewer should load and draw. On the *call-list track* it is an ordered list of calls
   to the PDBe Mol\* viewer. 258 requests are posed on both tracks with the
   same target atoms, so that an error of content can be told apart from an error of format.
4. **A pilot that corrected the benchmark, and a fixed plan for the final run** (Sections 6
   and 7). A pilot run on 15 models exposed a flaw in our own references
   and changed the design, and one final run will fill tables whose shape is already set.
   ⟦PENDING: final run — one sentence stating the main result⟧

Terms are defined where they are first used and collected in two boxes: Box 1, at the start
of Section 3, has the terms of variants, numbering and the corpus, and Box 2, at the start of
Section 4, those of grading and of the run.

## 2. Related work

Existing benchmarks that involve molecular viewers test agents that operate a desktop through
screenshots (ScienceBoard [9], OSWorld-Science [10]), or
score pictures with a judge model (SciVisAgentBench [11]). We found none that grades the atoms a viewer would draw against references
computed from the structure, and none that tests the mapping of residue numbers. Assistants
for molecular viewers exist, but their papers report no accuracy for driving the viewer.

### 2.1 Benchmarks that score the operation of scientific software

**ScienceBoard** [9] is the closest published benchmark. It has 169 tasks in
six domains, performed by agents that operate a desktop through screenshots and clicks. Its
biochemistry domain uses UCSF ChimeraX [12], and a task is checked by reading
the state of the application after the agent has finished. MolBench shares the idea of checking
the resulting state. It differs in four ways. It tests the step from request to commands
directly, with no desktop in between. Its references are computed by script and record their
origin. Four of its categories of task differ in what the model must know beyond the request, and
one of these asks about clinical variants. And it poses requests in two answer formats.

**SciVisAgentBench** [11] has 108 expert-written cases of scientific
visualization; its molecular cases use GROMACS and VMD. Outcomes are scored by a language-model
judge against written rubrics, with deterministic checks for some suites. The authors compared
the judge with 12 visualization experts and report an agreement among raters (Krippendorff's
alpha) of 0.669 and a correlation between judge and human scores of about 0.81. MolBench is
narrower and stricter: it covers only molecular viewers, and its scores need no judge model.

**OSWorld-Science** [10] follows the OSWorld desktop benchmark
[13] with 146 tasks over scientific applications, one of which combines PyMOL with a
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
modelling that can also operate PyMOL. **ChimeraX** can be operated from a chat assistant
through a built-in tool server; its documentation notes that the assistant "will often make
mistakes" [1]. **VOICE** [17] and a speech interface for an immersive
molecular-graphics application [18] operate molecular scenes by spoken language
and were evaluated with users, not with scored tasks. The Mol\* project has merged an optional
assistant and a command layer into its next viewer [2]; we found no published
benchmark from that work. A community tool that builds MolViewSpec scenes from chat
[19] states in its documentation that the residue numbers researchers take from
ClinVar, publications and mutation databases "are always author numbers". That holds for some
entries and fails for many [5]. It is the error our clinical category is built to
detect.

### 2.3 The data and software MolBench stands on

MolViewSpec describes a molecular scene as a tree of typed nodes and is implemented as an
extension of the Mol\* viewer [16, 20, 21]. The
call-list track targets the PDBe build of Mol\* [22], which a notebook widget exposes
to Python [23]. Structures come from the Protein Data Bank [24] and, for
5 predicted structures, from the AlphaFold Protein Structure Database [25, 26]. The mapping between UniProt residues and the residues of a structure
comes from SIFTS [8], as distributed by PDBe [27, 28]. Variants
and their clinical classification come from ClinVar [6], found through UniProt
[7]. Structure files are read with GEMMI [29].

The numbering problem at the centre of the clinical category has been met from another direction.
Vollmar and colleagues find residue mentions in the crystallographic literature and map them to
structures through SIFTS [30]. Their system reads papers; ours asks whether a
language model can do the same mapping when it writes a scene. MiSI-Bench [31] asks
vision-language models questions about rendered images of molecules and finds them well below
human level, which is one reason our scores do not rest on a model that looks at pictures.

Where this section says that another work lacks something, we mean that we did not find it in
the cited source.

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
| UniProt, canonical sequence | UniProt is the reference database of protein sequences. Each protein has an accession, such as P61626, and one sequence that UniProt picks as its reference, the *canonical sequence*. |
| ClinVar | A public archive of human genetic variants. Submitters, mostly clinical laboratories, send their classification of a variant for a condition, on a scale from benign through uncertain significance to pathogenic. For each *variation record* (accession beginning with VCV; usually one change at the level of DNA) ClinVar publishes an aggregate *germline* classification, such as "Pathogenic", and a *review status*. Germline variants are present in every cell of a person, inherited or newly arisen, as opposed to somatic variants that arise in a tumour. The review status says how far the classification has been reviewed (stated criteria, several submitters in agreement, an expert panel); it is not a measure of the strength of the evidence. Different DNA changes can give the same amino-acid change, so one amino-acid change can have more than one record. We write ClinVar's terms in lower case. |
| Transcript | A reference sequence of one messenger RNA of a gene, with an accession and a version number (NM_000239.3). ClinVar states each change on a transcript, in the form c.244T>C: nucleotide 244 of the coding sequence, counted from the A of the start codon ATG, changes from T to C. A gene can have several transcripts, and they can number the protein differently. |
| Missense variant; p.W82R | A change of one amino acid into another. p.W82R: the tryptophan (W) at position 82 becomes an arginine (R). The same in three-letter form is p.Trp82Arg. The prefix "p." marks a description of a change in the protein, as opposed to "c." for the coding DNA; it does not say which sequence the position is counted on. In this paper it is the UniProt canonical sequence, here P61626. HGVS, the nomenclature of the Human Genome Variation Society for naming variants, does not accept a UniProt accession as a reference sequence (Section 3.3.1). |
| Signal peptide, mature protein, traditional name | The *mature protein* is what is left after the cell has removed the leading part of a newly made protein. That part can be the first residue alone, the *initiator methionine* (haemoglobin beta); a *signal peptide* (lysozyme: 18 residues); or a signal peptide and a further segment, a *propeptide* (coagulation factor IX: 46 residues). Older literature often numbers residues from the first residue of the mature protein; we call a variant name of this kind a *traditional name* (the genetics literature also says legacy name) and its numbering *mature-protein numbering*. A traditional name carries no "p.", as in W64R. |
| Mol\*, MolViewSpec | Mol\* is an open-source molecular viewer that runs in a web browser. MolViewSpec is a format, written in JSON (JavaScript Object Notation), that describes what Mol\* should load and draw. PDBe Mol\* is the build of Mol\* maintained by the Protein Data Bank in Europe (PDBe). |
| Polymer, ligand | The *polymer* is the protein, DNA or RNA chains of a structure. A *ligand* is a small molecule bound to them. |
| Representation | A way of drawing atoms: *cartoon* (a ribbon that traces the whole polymer chain, the usual background of a picture), *ball-and-stick*, *spacefill* (every atom as a full-size sphere), *surface*. |

*Terms of the corpus.*

| Term | Meaning in this paper |
|:---------|:------------------------------|
| Author numbering | The chain identifiers and residue numbers chosen by the depositors (in the structure file: `auth_asym_id`, `auth_seq_id`). This is what papers and most viewers show. A number can carry an *insertion code*: a letter appended to it (52A) where the depositors placed an extra residue between two numbers. |
| Label numbering | The chain identifiers and residue numbers assigned by the archive (`label_asym_id`, `label_seq_id`). Residues are counted 1, 2, 3 … along the full sequence of the molecule that was studied, including residues that are not seen in the coordinates, so the count has no gaps and no insertion codes. |
| UniProt numbering | The position of a residue in the UniProt canonical sequence, counted from its first residue and so including any signal peptide. The variant names we use are in this numbering unless the request says otherwise (Section 3.3.1). |
| Offset | For one residue, its UniProt number minus its author number (82 − 64 = 18 in the running example). It can differ from residue to residue within a chain. A residue *has an offset* when the two numbers differ. In every clinical task with an offset the UniProt number is the larger one. |
| Copying the number | Using the number printed in a variant name as the author residue number, without converting it. Copying is *right* in a task if the answer written in this way is exactly right, and *wrong* otherwise. The property is defined on author numbering and is used to group results of the scene track only (Section 3.3.1). |
| Request, task, answer | The *request* is the plain-language instruction given to the model. A *task* is a request on one track, with its reference answer and, where it has one, its target; a request that is posed on both tracks is two tasks. An *answer* is what the model returns for one task. Each task is answered 3 times in the main condition. |
| Target | The atoms that the request is about. Most tasks store it. For a request that only changes a viewer setting or hides something, the target is everything the reference changes; 31 follow-up tasks have none (Section 4.2). |
| Scene | An answer in MolViewSpec: a description of what to load and how to draw it. A scene groups the atoms it selects into *components*; each component is a named set of atoms that is then drawn in one or more ways. Nothing is on screen unless the scene says so. |
| Call list | An answer as an ordered list of calls to the PDBe Mol\* viewer, written in JSON (Section 3.4). |
| Default view | What the call-list viewer draws as soon as a structure is loaded, before any further call: the whole structure, with the polymer as a cartoon. A scene has no default view; its screen starts empty. |
| Track, format | A *track* is one of the two halves of the benchmark. *Scene track*: answers are MolViewSpec scenes. *Call-list track*: answers are call lists. *Format* means the answer language itself (MolViewSpec, or PDBe Mol\* calls). |
| Pair, side | A *pair* is one request posed on both tracks, with the same target atoms. A *side* is one of the two tasks of a pair. Both words are used for nothing else in this paper. |

</div>

### 3.1 Frozen public data

**Structures.** All tasks use a fixed *structure panel* of 79 structures, namely
74 PDB entries [24] and 5 predicted structures from
the AlphaFold Protein Structure Database [25]. One PDB entry,
1HSG, is reserved for the worked example of both system prompts,
so tasks use 78. The panel was chosen for
coverage, not at random: proteins alone, with bound small molecules or metal ions, with DNA or
RNA, with attached sugars, and membrane proteins. The 5 predicted structures are of
p53, gamma-crystallin D, calmodulin-1, lysozyme and haemoglobin beta; each of these proteins also has an experimental structure in the
panel, and a predicted structure uses UniProt numbering. In 46 of the
79 structures at least one residue has an offset: its author number differs from its
UniProt number. Every
feature that we claim for an entry is verified in its file by the build script, or the build
fails. The Supporting Information (SI, Section S3) lists the panel, its features and its
selection rule.

**Disease proteins and variants.** The panel includes structures of
27 human proteins in which germline missense variants cause
Mendelian disease, that is, disease caused by changes in a single gene (missense: one amino
acid is replaced by another; germline: the variant is in every cell of a person). We chose the proteins by hand, as familiar
examples that have experimental structures. For each protein, one PDB entry was then chosen
by a scripted rule that did not look at how the entry is numbered (SI Section S3). A protein
can still have tasks on more than one structure: on its chosen entry, on its predicted
structure where the panel has one, and on another panel entry that also contains it (two
haemoglobin entries hold both the alpha and the beta chain). In all,
6 proteins have tasks on more than one structure.

**The pool of variants.** UniProt lists 3,352 missense variants of
these proteins as pathogenic or likely pathogenic. We keep a variant only if at least one
ClinVar record that UniProt cross-references passes two tests; we call such a record a
*qualifying record*.

1. The record gives the same amino-acid change a pathogenic or likely pathogenic aggregate
   germline classification. 657 candidates have no such record.
2. The record is of the gene named in the request, describes that change alone, and states
   the criteria of the classification. A further 295
   candidates have a record that passes the first test but none that passes both.

The remaining 2,400 variants form the pool. We did not search ClinVar beyond
UniProt's cross-references. SI Table S4 gives the filter step by step, and SI Section S3.2
the dates on which the data were read.

**What a request says about the classification.** ClinVar classifies DNA-level records, each
for a stated condition; it does not classify protein changes as such. When a request says
that a protein-level variant "is classified as pathogenic in ClinVar", it means that at
least one qualifying record of this amino-acid change carries that classification. The
request names no condition and no DNA change. It repeats ClinVar's aggregate value in lower
case: "pathogenic", "likely pathogenic" or "pathogenic/likely pathogenic". Where the
qualifying records behind one request carry different values, it says "pathogenic or likely
pathogenic" (7 of the 82 requests). The classification is
always the germline one, also for variants that are better known as somatic changes in
tumours, such as *TP53* p.Arg175His.

Two exceptions were made by hand (SI Section S3.2). One well-known lysozyme variant,
p.Ile74Thr, is used in one task per track although its ClinVar
record states no criteria and it is therefore outside the pool. One *APOE* variant inside the
pool is never asked about, because it is better known for a reported protective effect.

**From the pool to the clinical tasks.** A clinical task asks about one variant, or a few, on
a panel structure of its protein. The generator picks the variant by seeded random choice
among the pool variants whose residue is observed in the structure (present in its
coordinates; flexible parts of a chain are often missing from them) with the amino acid that
the UniProt canonical sequence has at that position. For 9 proteins a well-known variant, named by
hand before generation, is tried first (for example the sickle-cell variant of haemoglobin
beta, p.Glu7Val; SI Section S3.2 has the list). The result is
82 tasks per track on 25 proteins and 31
structures: 26 PDB entries and the 5 predicted
structures. There is one PDB entry more than there are proteins, because
23 proteins have tasks on one PDB entry each and the two
haemoglobin chains on three between them. There are at most 6 tasks per track on one structure.
The other two proteins have no task, because no
variant of the pool is observed in their panel structure (SI Section S3.2).

**Atom tables and residue mapping.** For each structure we freeze two tables. The *atom table*
is built from the entry's file in the PDB archive (for a predicted structure, the file of the
AlphaFold Protein Structure Database). It lists every atom record of the first coordinate set
(the first "model" in PDB terms; we avoid that word because *model* here means a language
model), hydrogen atoms included where the file has them, with its chain and residue in both
author and label numbering. The *mapping table*
holds the SIFTS correspondence between each observed residue and its UniProt position.
Generators and graders read only these tables, and nothing is fetched while a task is built
from the tables, graded or loaded. The atom table is compared with what the viewer itself
selects in the same file (Section 3.7); SI Section S3.1 gives the details.

### 3.2 From data to a task: the running example

The clinical generator produced the running example in six steps.

1. **Variant.** From the pool it picks the *LYZ* variant p.W82R
   (p.Trp82Arg; UniProt P61626). Through UniProt's cross-references we found
   2 ClinVar records of this protein change, one for each of the two
   single-nucleotide changes that turn the codon of this tryptophan (the three nucleotides that
   encode it) into a codon of arginine (VCV000014376, NM_000239.3(LYZ):c.244T>C (p.Trp82Arg); VCV000014378, NM_000239.3(LYZ):c.244T>A (p.Trp82Arg)). As read on 16 November 2026, both
   are classified as pathogenic, each with the review status
   "criteria provided, single submitter": each record has one submitter, who stated criteria, and no
   second submitter or expert panel has confirmed it. The field of the
   record that names the condition reads "not provided".
2. **Structure.** The panel entry for P61626 is 2NWD, human lysozyme.
3. **Mapping.** The mapping table says that UniProt positions
   19–148 are author residues
   1–130 of author chain X: an offset of
   18, the length of the signal peptide. Position 82 is
   therefore author residue 64 (label chain A, label residue
   64).
4. **Identity check.** The atom table must hold, at that residue, the amino acid that the
   UniProt canonical sequence has at the position. It does: Trp64, 24 atom
   records (14 non-hydrogen atoms and 10
   hydrogens; this entry was measured in enough detail, at 1.04 Å resolution, to
   include hydrogens). Had
   the protein in the entry carried another amino acid there, the variant would not be offered
   for this entry.
5. **Wording.** A seeded random choice picks one of the template's three wordings, the colour
   (yellow) and the representation (spacefill spheres). The request names the entry, the gene,
   the UniProt accession and the variant. It never says which residue of the entry is meant.
6. **Reference, twice.** The script writes the reference scene (author chain
   X, author residue 64, yellow spacefill spheres) and the
   reference call list (load the entry; draw UniProt P61626 position
   82 as yellow spacefill spheres). The 82 is correct
   there: the call-list viewer has a selector that takes a UniProt position and converts it
   to the residue of the file itself, which a scene cannot do (Section 3.4). The script then
   confirms that both references resolve to the same 24 atoms, and stores
   them as the target of both tasks.

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
129 templates; SI Section S2 lists every template with an example and
says how the tasks of a category are spread over its templates.

![**Figure 2. The eight categories of task, with one request each.** Counts are tasks on the scene track / the call-list track; a dash means that the category has no task on that track (Table 1 gives the reasons). Requests are quoted from the corpus; a long one is cut short. Two words in them are file terms: a *het group* is a molecule in the entry that is not part of a polymer chain, such as a ligand, named by an identifier of up to three characters; *C-alpha* is the central carbon atom of an amino acid. Left column: the four categories that differ in what the model must know beyond the request. Right column: the four that differ in the form of the task. Framed in blue: the two *lookup categories*, name resolution and clinical variant, in which the answer needs one piece of information that a person would look up in a database and that the model must recall.](generated/fig_tiers.svg)

*Categories that differ in what the model must know.*

- **Translation.** Everything needed is in the request: the entry, the chains, the residue
  numbers, the colours. The model only has to write it in the format.
- **Structure-grounded.** The request names a feature, such as the ligand, the disulfide bonds
  (links between two cysteine residues) or the residues that hold a metal ion. The model does
  not see the file. It must either use a generic selector of the format where one fits (for
  example "ligand") or recall what the entry contains, such as the identifier of the ligand
  or the numbers of the residues. The references are computed from the entry's own records.
- **Name resolution.** The request names a protein, not an entry ("a structure of human p53
  bound to DNA"), and the model must choose an entry. Any entry on a frozen list of the PDB
  entries of that protein is accepted (SI Section S4.4 gives the rule and the date of the
  list). An answer on an accepted entry outside the structure panel is graded by a weaker
  rule (Section 4.1).
- **Clinical variant.** As in the running example: the request names a variant, and the model
  must find its residue in the structure, where its number often differs from the one in the
  name. Section 3.3.1 describes this category.

*Categories that differ in the form of the task.*

- **Interactions.** As in translation, the request states everything, so nothing more must be
  known about the structure. What differs is what must be written: single atoms are selected,
  not whole residues, and something is drawn between or around them, such as a hydrogen bond
  as a dashed line labelled with its length, with the camera centred on it.
- **Follow-up turn.** The model receives a start state, written as a scene or a call list in
  the format of its answer, and an edit request ("make the magenta chain plum"). It returns
  the complete new state. Only the resulting drawn state is graded, so an answer that makes
  the edit but drops something from the start state, such as the colour of another chain,
  fails. In 10 scene tasks and 8
  call-list tasks the right answer is the start state returned unchanged. In most of these
  the edit asks for something that the start state already shows ("Hide the waters."
  when the start state has already hidden them). In 2 scene tasks the edit asks for a spin,
  which a scene cannot express, and the request itself says to change nothing in that case.
- **Several right answers.** The request leaves one countable thing open. "Colour Lys29
  yellow" in an insulin entry with two B chains can mean either copy or both. The script lists
  every *accepted answer* (a median of 3 per task on the
  scene track), and an answer that matches any one of them is right.
- **Viewer settings.** Settings that only the call-list format can express, such as the
  background colour and spin.

Name resolution and clinical variant are the *lookup categories*. In both, what the request
leaves out is one piece of information that a person would look up in a database: which entry holds the
protein, or which residue number the variant has in the entry. The model cannot look it up and
must recall it. Only these two categories have a grounding pack, in which the lookup has been
done for the model (Section 5.2).

**Table 1. The corpus.** Tasks per category and track, written as total (tasks on the other
structures + tasks on the 15 *set-aside structures*, which no
earlier release of the benchmark used; these tasks are public too and are not a hidden test
set; Section 3.6). *Pairs*: requests posed on both tracks with the same target atoms. A dash means
that the category has no task on that track. For interactions (on the call-list track) and
viewer settings (on the scene track) the format cannot express what is asked. Name resolution
could be asked on the call-list track but is not: the call-list grader has no atom table for
an entry outside the panel (Section 3.4).

| Category | What is asked | Scene track (other + set-aside structures) | Call-list track (other + set-aside structures) | Pairs |
|:---------|:----------------|-----:|-----:|--:|
| ***Differ in what the model must know*** | | | | |
| Translation | Everything needed is in the request; write it in the format. | 73 (55 + 18) | 178 (138 + 40) | 62 |
| Structure-grounded | The request names a feature (the ligand, the disulfides); the model must know which atoms these are. | 63 (52 + 11) | 63 (52 + 11) | 63 |
| Name resolution | The structure is named by protein, not by identifier. | 39 (32 + 7) | – | – |
| Clinical variant | A variant is named in UniProt numbering or in mature-protein numbering; its residue must be found in the structure, where its number often differs. | 82 (63 + 19) | 82 (63 + 19) | 82 |
| ***Differ in the form of the task*** | | | | |
| Interactions | Named atoms and a measurement or contact between them. | 40 (32 + 8) | – | – |
| Follow-up turn | A start state plus an edit request; the full new state is returned. | 58 (50 + 8) | 44 (34 + 10) | 36 |
| Several right answers | The request leaves one countable thing open; several drawn states are right. | 26 (21 + 5) | 15 (11 + 4) | 15 |
| Viewer settings | A viewer setting that only the call-list format can express. | – | 34 (29 + 5) | – |
| **All** | | **381** (305 + 76) | **416** (327 + 89) | **258** |

The 797 tasks (381 on the scene track, 416 on the
call-list track) use 78 of the 79 panel structures. No structure
appears in more than 6 tasks of one category and
track. The call-list track has more translation tasks than the scene track because its format
has many single-purpose calls and selectors. Of its 178 translation
tasks, 116 (from
18 templates) exercise calls that have no
counterpart in a scene; the other 62 are pairs.

#### 3.3.1 The clinical category

There are 82 clinical tasks per track, on 25 proteins and
31 structures. Of these, 74 name one variant; the other
8 name several, up to 4. In all, the requests
name 87 distinct variants; a variant that is asked about on two structures
(matched tasks, below) is counted once. No target residue has an insertion code.

*How variants are named.* The requests use three forms of name. Three-letter names
(p.Trp82Arg) and one-letter names (p.W82R) carry the prefix "p.". In this
corpus a name with "p." is always in UniProt numbering; the prefix itself does not say so.
*Traditional names* (W64R) carry no prefix and are in mature-protein numbering,
as in older literature. Names with "p." follow the protein-level style of the HGVS
nomenclature [32, 33], but they are not complete HGVS descriptions:
a complete description names a versioned reference sequence, and a UniProt accession, which
46 requests state, is not one that HGVS accepts. ClinVar itself
states each change on a transcript, and we did not check which transcript its protein-level
name is counted on. SI Section S3.2 gives the details of both points, and Section 9.2 the
limit that follows.

The request asks for the residue in one of three wordings: "the residue it replaces", "the
residue replaced by" the variant, or "the wild-type residue at the position of" the variant.
All three mean the amino acid that the UniProt canonical sequence has at that position; the
third uses "wild-type", the usual word in structural biology, where clinical genetics would
say "reference".

*Traditional names.* A traditional name is used in 13 requests (for
example transthyretin V30M, which is p.Val50Met). Each of these requests says so, and says
what mature-protein numbering leaves out. One of them in full:

> *"In PDB entry 8CE0, show the residue replaced by the likely pathogenic APOE (Apolipoprotein E) variant R136L (ClinVar) as green ball-and-stick. The name R136L is in mature-protein numbering: residues are counted from the first residue of the mature protein, that is, after the 18-residue signal peptide."*

In UniProt numbering this variant is p.Arg154Leu. Entry
8CE0 is numbered from the mature protein as well, so here the
printed 136 is the author residue number, and copying it is right.
SI Section S3.2 says what each of the 13 traditional names leaves out.

*Two groupings.* Each clinical task has two yes-or-no properties that matter for the results.
They are not the same property (Table 2a).

- **Copying the number** (the grouping on which the question of the Introduction is
  answered). If an answer uses the number printed in the
  variant name as the author residue number, is it right? Copying is right in
  34 tasks and wrong in 48. The property
  describes what copying does on the scene track, where the model must give an author or a
  label number. On the call-list track the printed number can also be passed unchanged to
  the viewer's UniProt selector (Section 3.4), so results are grouped by this property on
  the scene track only (Section 6.4).
- **Offset** (reported for description only). Does the author number of the target residue differ
  from its UniProt number? An offset is present in 59 tasks
  (72%) and absent in 23. Where there is one, the
  UniProt number is always the larger, by 1 to 216
  residues.

A task with several target residues is assigned by rule. Copying counts as right only if the
answer with every number copied is exactly right, that is, if copying is right for every named
variant. The task has an offset if any of its target residues has one. Some tasks also ask
for the helix or strand that contains the residue (helices and strands are the two common
local shapes of a protein chain; the entry records where each begins and ends). In such a
task both properties are those of the variant's residue, not of the whole helix or strand. As it turns out, all 8 tasks with several variants and all
10 helix or strand tasks have an offset, and copying is wrong in all of them.

**Table 2a. The two groupings of the 82 clinical tasks, crossed.** *Copying the number*:
an answer that uses the number printed in the variant name as the author residue number is
right, or wrong. *Offset*: the author number of the target residue differs from its UniProt
number, or does not. A task with several target residues has an offset if any of them has
one, and copying is right in it only if it is right for all of them.

| | Copying the number is right | Copying the number is wrong | All |
|:-----------------|---:|---:|---:|
| **No offset**: the target's author number is its UniProt number | 22 | 1 | 23 |
| **Offset**: the target's author number differs from its UniProt number | 12 | 47 | 59 |
| **All** | **34** | **48** | **82** |

With a name in UniProt numbering, copying is right exactly when there is no offset. The two
groupings differ only for the 13 traditional names. In
12 of them the entry is also numbered from the mature protein, so
the number in the name is the author number although the UniProt number is not. The one
remaining traditional name (E6V of haemoglobin beta, which
is p.Glu7Val) is asked on a predicted structure, which
uses UniProt numbering. There, copying the traditional number selects the wrong residue
although the target has no offset (the single task in the top-right cell of Table 2a).

*Further properties.* Table 2b lists further properties of the clinical tasks. One needs a
remark. Where a request states no UniProt accession and names the variant with "p.", neither
the request nor the system prompt says which sequence the position is counted on. A reader of
a bare name with "p." would normally take it to be counted on the protein of the gene's MANE
Select transcript, the one transcript per gene that RefSeq and Ensembl jointly designate as
the default for clinical reporting [34]. We assume, and did not check, that
this protein is numbered as the UniProt canonical sequence is (Section 9.2).

**Table 2b. Further properties of the 82 clinical tasks.** *Tasks*: number of tasks
per track with the property. Indented rows divide the row above them. *Traditional name*: a
name in mature-protein numbering, without "p."; the request then says how the name is
numbered.

| Property of the task | Tasks | Why it matters |
|:-------------------------|--:|:--------------------------|
| The request states the UniProt accession, as the running example does | 46 | On the call-list track the accession can be passed on to the viewer (Section 3.4). |
|  of which: name in UniProt numbering / traditional name | 39 / 7 | |
| The request states no accession | 36 | The model must know the accession to use the UniProt selector. |
|  of which: name in UniProt numbering / traditional name | 30 / 6 | |
| The entry holds several copies of the protein, and the request says which are meant | 35 | The chain identifier must be right as well as the number. |
|  of which: "in every chain that has it" / one named chain ("in chain B only") | 21 / 14 | With "every chain", the target is the residue in all of those chains; an answer that draws it in one chain only is not target-right. |
| The author chain identifier differs from the label chain identifier | 25 | The two numberings must not be mixed. |
| A cartoon of the structure is also asked for, in words | 29 | The reference then holds the cartoon, and on the scene track task success requires it. |
| The helix or strand that contains the residue is also asked for | 10 | The model must also know where the entry records that helix or strand to begin and end; these tasks are reported apart. |

*Matched tasks.* On each track, 20 of the 82 tasks form
10 sets of two *matched tasks*, which ask about the same variant on
two structures of one protein. In 8 of these sets one structure has an
offset and the other, always a predicted structure, has none. Both tasks of a set name the
variant in the same form. In 7 of the
8 sets the name is in UniProt numbering, so copying is wrong on the
structure with the offset and right on the predicted structure; Section 6.4 reports these
7 sets. The eighth set uses the traditional name
E6V of haemoglobin beta, and there it is the other way
round: copying is right on the PDB entry and wrong on the predicted structure. In the other 2
sets, both of p53, neither structure has an offset (the PDB entry uses UniProt numbering);
they are not reported apart.

### 3.4 The same request in two formats

A wrong answer has two possible causes: the model did not know which atoms were meant, or it
knew and could not write them in the format. One format cannot separate the two. MolBench
therefore poses 258 requests (68% of the scene
tasks) on both tracks, with identical wording and the same target atoms (Figure 3).

The two formats differ in kind. A MolViewSpec scene [20] is *declarative*: a tree
that states what to load, which atoms form a *component* (a named set of selected atoms), and
how each component is drawn.
Nothing is on screen unless the scene says so. A call list is *imperative*: an ordered list of
calls to the PDBe Mol\* viewer, version 3.3.2 [22]. The viewer starts with the whole
structure drawn in a *default view*, and each call changes that state, so order matters. The
call list is written as a JSON list in a small notation of our own, which the format guide
documents (Section 5.2). Each item names one call or setting of the viewer and its arguments,
under the names that the viewer's Python notebook widget, ipymolstar 0.1.0 [23],
gives them. The model does not write JavaScript or Python, and the grader follows what PDBe
Mol\* 3.3.2 does with each call.

The formats also differ in what they demand for a clinical request, and we state this openly
because it shapes the comparison. The viewer behind the call-list track can select a residue by
UniProt accession and position and does the mapping itself. A scene has no such selector: the
model must produce author or label numbers. Any selection that the format allows is accepted
if it resolves to the right atoms: author or label numbering on the scene track, and those
two or the UniProt selector on the call-list track. On the call-list side of a clinical pair,
a model can thus be right without knowing any residue number of the entry. When the request
states the accession and the name is in UniProt numbering (39 of
the 82 clinical requests), the model only has to pass both on to the right call.
When no accession is stated (30), it must also know the
accession.

The 13 requests with a traditional name are a separate case. Their printed
number is not the UniProt position, so the UniProt selector gives the wrong residue if the
number is passed on as printed. In 12 of them the printed number is
the entry's author number, and selecting by author number is right on either track; in the
remaining one the model must convert the number on either track. The format guide of the call-list track documents the UniProt selector, and the
guide of the scene track documents selection by author and by label numbering; neither says
how a given structure is numbered (Section 5.2).

The grader resolves the UniProt selector through the frozen mapping table. UniProt selections
on PDB entries were not replayed in the viewer, so there the agreement between grader and
viewer rests on both using SIFTS (Section 9.3).

![**Figure 3. One request, two formats, the same target atoms.** The scene and the call list are shown in shortened form. Below: for each model, every pair falls into one of four cells by whether each side is right. In the scene, "structure model" is MolViewSpec's name for the deposited coordinates and has nothing to do with a language model. The primary comparison counts a side as right when at least 2 of its 3 answers are *target-right*, that is, have a target score of exactly 1: the requested style is on the requested atoms and on no others, and unrequested background is ignored. It uses the 250 pairs that have a target score; it is repeated with task success in place of the target score, on all 258 pairs (Section 5.4). McNemar's test compares the two shaded cells, in which the model was right in one format only.](generated/fig_twins.svg)

Pairs exist in five categories: translation (62), structure-grounded
(63), clinical (82), follow-up
(36) and several right answers (15). The
other 123 scene tasks have no partner on the call-list track. Either the
call-list format cannot draw what they ask for (a distance line, a text label, a transparent
surface), or they are name-resolution tasks, in which the model chooses the entry and the
call-list grader has no atom table for an entry outside the panel.

Pairs are compared on the target score first, because task success is not the same test in
the two formats (Section 4.2 gives the reason, Section 5.4 the analysis).

In 15 pairs the reference call list contains an extra call
that switches off part of the default view, a call that a scene never needs. All of these
are first requests, not follow-up turns. In 9 of them the request
asks for something to be shown alone, or for part of the structure to be hidden
("Load 1AKE and show only chain A, as a teal cartoon."), and the call list must contain the call. In the other
6 the request asks for the whole protein as a surface or as
spacefill spheres; the reference switches off the default cartoon, and a call list that leaves
the cartoon in place is accepted as well. The paired analysis is reported with and without
these 15 pairs.

### 3.5 What a request may leave open

Requests written by people leave things unsaid, and a benchmark must decide what silence
means. We use one rule: **an attribute that the request does not state is free; one that it
states must match.** If the request gives no colour for a ligand, the grader ignores the
colour, and any colour is accepted. If the request says
"green", only green is right. Where the open point is which atoms are meant, the task lists
every accepted answer (Section 3.3, several right answers).

The same holds for the representation. On the scene track nothing is drawn unless the scene
names a representation, and every first request states one for each thing it asks to be
drawn, with one exception: 3 tasks of the category with
several right answers name none for a ligand
("Open 1MBN with the protein as a cartoon, and show the heme in blue."), and they list the ligand in each
representation as an accepted answer. On the call-list track a request can state a colour
alone, for a chain or a residue: the atoms are already drawn in the default view, and the
reference only recolours them. Opacity is not covered by the rule. A reference is opaque
unless the request states an opacity, which 9 tasks do, and an
answer that draws a requested style with another opacity earns half credit for it (Section
4.2).

The rule covers attributes of what was requested. Additions to the picture, such as a cartoon
that the request does not mention, are not covered by it; Section 4.2 says how they are
scored.

### 3.6 Set-aside structures; wording

MolBench tasks have been public since May 2026, so a model released later may have seen
earlier tasks. By *earlier* tasks and releases we mean those published before the present
corpus (the first version of the benchmark, Section 6). Two measures address this.

*Set-aside structures.* Before generation, 15 structures were
set aside: no earlier MolBench release used them, and their tasks are reported apart. The
165 tasks on them (21% of the corpus) form
the *set-aside split*. The other 632 tasks sit on
63 structures, of which
23 appeared in earlier MolBench tasks (scene tasks
or call-list tasks of any release of the first version; its pilot run, of scene tasks alone, used
14) and
40 did not.

The split compares two sets of structures. It does not compare seen tasks with unseen tasks:
nearly all tasks in both parts were generated for this version. Nor is the set-aside split a
hidden test set: the corpus was developed in a public repository, so its tasks were online
for some days before the final run. Three set-aside structures share a protein with one of
the other structures.

*How we read it.* A clearly lower score on the set-aside structures would suggest that scores
on the other structures profit from earlier tasks on them or from their being better known. A
difference near zero would not show the opposite. We report the difference with an interval
and do not test it, because the split is small (Section 9.4).

*Wording.* To measure sensitivity to wording, 30 requests on
structures outside the set-aside split have, beside their original (*full*) wording, two further phrasings each, a
*terse* one and an *indirect* one, with the same reference. For example, the request "Add chain B too, as a cartoon in grey." also exists in
a terse form ("chain B too, grey cartoon") and in an indirect form
("Could I see chain B as well? A grey cartoon would be fine."). Of the
30 requests, 11 are pairs, so they are
41 tasks, and two further phrasings of each give
82 additional task files. These are not counted in Table 1.

### 3.7 Checks on the corpus

Four checks involve no model (Figure 1).

- **Reference against structure.** Every reference must select at least one atom, must name the
  residue that the generator intended, and must grade as exactly right against itself. Every
  accepted answer must do the same.
- **Atom tables against the viewer.** Selections were read back from the running viewers
  (Mol\* 5.9.0 and PDBe Mol\* 3.3.2) and compared atom for atom with the atom tables. All
  agreed. Section 4.5 gives the numbers and lists what was not checked.
- **Grader against a control set.** The grader is run on 2,175 answers whose
  verdict is known (Section 4.5).
- **Format rules.** One script validates every task file against the written task format, and
  the run does not start unless every check passes.

## 4. Grading on drawn state

The grader turns the reference and the answer into what the viewer would draw (for every
atom, its representations and colours) and compares the two. Each answer gets three scores:
F1 (how much of the drawing is right), task success (the drawing is exactly right) and a
target score (how far the requested style is on the requested atoms and on no others, with
unrequested background ignored). Box 2
defines these terms and those of the run. Sections 4.1 to 4.4 give each in full, and Section
4.5 tests the grader itself. Grading always compares two drawn states, that of the reference
and that of the answer; where this section says *the other*, it means the other of these two.

<div class="box">

**Box 2. Terms and notation: grading and the run.**

| Term | Meaning in this paper |
|:---------|:------------------------------|
| Style | One representation with one colour and one opacity, for example "grey cartoon, opaque". |
| Drawn state | For every atom of the structure, the set of its styles, plus a few facts about the whole scene (labels, distance lines, the atoms the camera is centred on, viewer settings such as the background colour). On the call-list track: the changes from the default view. |
| Fact | One unit of the drawn state: all atoms that carry the same set of styles form one fact; each label, each distance line and each viewer setting that differs from the default is one fact. Atoms that are not drawn belong to no fact. |
| F1 | How much of the drawn state is right, from 0 to 1, with partial credit. For each fact of the reference, take the fraction of it that the answer also draws; *recall* is the mean of these fractions. *Precision* is the same in the other direction, over the facts of the answer. F1 is the harmonic mean of the two. |
| Task success | For one answer, yes or no: the drawn state is exactly right, with nothing missing and nothing extra. The *task success rate* of a model is the share of its answers that succeed. |
| All-3 rate, majority | *All-3 rate*: the share of tasks on which all 3 answers succeed. *Majority*: at least 2 of the 3 answers are right; used only in the comparison of pairs. |
| Target score | From 0 to 1: how far the requested style is on the target atoms and on no others. Unrequested background, such as a cartoon of the protein, is ignored. An answer is *target-right* when its target score is exactly 1. |
| Primary score | The score on which a table or a comparison is read first. *Within a track* (Tables 6 to 8, 11 and 12): the task success rate, strict. *Between the two formats* (Table 9a) *and for copying against mapping* (Table 10): the target score, because task success is not the same test on the two tracks and also falls when an answer adds unrequested context. The comparison of pairs on the target score is the *primary comparison* (Table 9a), and the one on task success the secondary (Table 9b). F1 is reported for partial credit and is never primary. |
| Unrequested context | Drawing that the request did not ask for, such as a cartoon of the protein behind a requested residue. |
| Valid, invalid | An answer is *valid* if it obeys the answer format and the viewer can show it: on the scene track, a scene that Mol\* accepts and whose structure file it can load; on the call-list track, a JSON list in which every call and every field is documented. Otherwise it is *invalid*, in one of two ways. An *unshowable* answer cannot be shown at all and scores 0. A *schema-breaking* call list contains parts that the viewer ignores; it is graded as the viewer would treat it but is not counted as valid (Section 4.4). |
| Call schema | The list of calls that the format guide documents, with the type of each field. A call list *fits* it if every call is on the list and every field has the documented type. |
| Strict, valid-only, repaired | Three ways to average a score (Section 4.4). *Strict* (the default): every answer counts. *Valid-only*: the mean over valid answers. *Repaired*: strict, after unparseable answers have been passed through an offline JSON repair. |
| Control, control set | A *control* is a reference and one answer whose verdict is known from how the answer was made; the *control set* is all 2,175 of them (Section 4.5). |
| Format guide | The frozen text in the system prompt that documents the answer format (Section 5.2). |
| Grounding pack | The result of an offline lookup for one task, appended to the request in one prompting condition (Section 5.2). |
| Core models, optional models | The 16 models that are always run, and up to 5 larger ones (Section 5.1). |
| Keyword script, literal script | Two scripts that use no model. The keyword script maps words of the request to fixed answers by rule. The literal script writes what the request spells out and uses every number as written. They mark the scores that need no skill and no lookup (Section 5.1). |

</div>

### 4.1 From an answer to a drawn state

An answer is graded by what the viewer would show, not by how the answer is written. The
grader turns the reference and the answer into a *drawn state*: for every atom of the
structure, the set of its *styles* (a style is one representation with one colour and one
opacity), plus a few facts about the scene as a whole. It does so with the frozen atom tables
and with the rules of the viewer itself, which we read back from the running viewer and did not
take from documentation. Two examples of such rules: a cartoon draws only polymer residues, so
a cartoon of "everything" and a cartoon of "the polymer" are the same drawing; and a cartoon
requested for a ligand is drawn by Mol\* as ball-and-stick, and is graded as that. No browser
runs and nothing is fetched while grading.

The drawn state is cut into *facts* of equal weight. All atoms that carry the same set of
styles form one fact. "The protein as a grey cartoon, with one residue also as red
ball-and-stick" is two facts: the atoms of that residue (grey cartoon and red ball-and-stick),
and all other protein atoms (grey cartoon only). Atoms that are not drawn belong to no fact.
Each text label, each distance line and, when the request asks for a focus, the set of atoms
that the camera is centred on is a further fact. So is each viewer setting that differs from
the default, such as the background colour or spin; it is right if reference and answer have
the same setting.

Loading the right entry earns nothing by itself. On an entry that the task does not accept,
nothing can be compared, and every score is 0.

One category is a partial exception to grading on drawn state. A name-resolution task
accepts any PDB entry of the named protein, and we hold atom tables only for panel entries.
The 39 tasks accept 5,778 entries in all:
their 39 reference entries, 3 further
panel entries, and 5,736 entries outside the panel. An
answer on a panel entry is graded on drawn state. An answer on an accepted entry outside the
panel has no atom table to be resolved on: its selections are compared with the reference's
as written, and all three scores of Section 4.2 come from that comparison. The common ways
of writing "the protein" pass; a correct selection that is spelled differently, for example
by chain identifier, fails. This is the *weaker rule* of the name-resolution category. The
run records for each answer whether its entry is the reference entry, so results are
reported in two rows: answers on the reference entry, and answers on any other accepted
entry, nearly all of which fall under the weaker rule (Table 8).

On the call-list track the grader replays the calls in order, following the behaviour of PDBe
Mol\* 3.3.2, and compares the drawn state that they end in. Because that viewer draws the whole
structure as soon as it loads, the facts of a call-list answer are its *differences from the
default view*. Order matters, as it does in the viewer: a later call can undo an earlier one,
and the answer is graded on where it ends. SI Section S4 lists every rule on both tracks.

### 4.2 Three scores

Each answer receives three scores. They answer different questions, and Section 4.3 shows them
parting on the running example.

**F1: how much of the drawn state is right?** A fact is matched atom by atom against the
other drawn state. For each atom of the fact, take the share of the atom's styles that the
other drawn state also has on that atom; a style with the right representation and the wrong
colour or opacity counts half. The *fraction* of the
fact is the mean of these shares over its atoms. A cartoon counts as a style of every atom of
each residue that it traces. *Recall* is the mean of the fraction over the facts of the
reference: how much of what was wanted the answer has. *Precision* is the same over the facts
of the answer: how much of what the answer drew was wanted. F1 is the harmonic mean of recall
and precision, from 0 to 1. Missing drawing costs recall, and unrequested drawing costs
precision. Facts count equally whatever their number of atoms: one unrequested cartoon costs
the same precision on a small protein as on a large one.

On the call-list track a fact about atoms is a group of atoms that the calls changed from the
default view in the same way. Here the grader compares the final appearance of each atom as a
whole, not style by style. The rule differs because the two formats do: a scene lists the
styles that it adds to an empty screen, so styles can be matched one by one, whereas a call
changes atoms that are already drawn, and what can be compared is how each changed atom ends
up. An atom scores 1 if it ends up drawn exactly as in the other drawn
state, one half if reference and answer both changed it but to different results, and 0 if
only one of the two changed it. Example: the right residue drawn red where yellow was
asked for is changed by both, differently, and scores 0.50 (Table 3, row
C4; SI Section S4.6). The call-list rule is more generous than the scene rule: on
the call-list track any change to the right atoms earns one half, even in the wrong
representation, where on the scene track the wrong representation earns nothing. F1, like
task success (below), is therefore not the same measure on the two tracks, and we never
compare it between them.

**Task success: is the drawn state exactly right?** For one answer, task success is yes or
no: yes if recall and precision are both 1 on an entry that the task accepts, so that every fact of the
reference is present and the answer has no other. For a model, the *task success rate* is the
mean over tasks of the share of the task's 3 answers that succeed. Every task
has the same number of answers, so this equals the share of all the model's answers that
succeed. This is the primary score within a track, because a viewer scene is either the one
that was asked for or it is not. Two
further summaries are used and always named: the *all-3 rate*, the share of
tasks on which all 3 answers succeed, and *majority*, used only in the paired
analysis, where a side of a pair counts as right if at least 2 of its 3 answers
are (Section 5.4).

**Target score: is the requested style on the requested atoms, and only there?** The *target*
of a task is the atoms that the request is about. For most tasks the generator stores it with
the task. In a
clinical task it is the residue of the variant. In a task that asks for a feature against a
background ("grey cartoon and the biotin in green ball-and-stick") it is the feature, here the
biotin and not the cartoon; if several features are asked for, it is all of them. In a task
with no such distinction ("the whole protein as a yellow cartoon") it is everything the
reference draws.

The target score, from 0 to 1, asks whether the requested styles are on the target atoms and
stop there. It counts *items*: one item is one style on one atom. Three counts describe what
the answer did with the requested styles.

- *Wanted*: the requested styles on the target atoms.
- *Credit*: 1 for each wanted item that the answer has, and one half for each that the answer
  draws in the right representation with another colour or opacity, in a style confined to
  the target.
- *Attempted*: the wanted items that the answer drew in the right representation, in any
  colour or opacity, in a style confined to the target.

Whatever else the answer draws is sorted by three rules. Rule 1 gives a fourth count,
*spill*, and rule 2 a fifth, *extra*; drawing under rule 3 is ignored.

1. *Spill.* A style of the answer (one representation in one colour and opacity) that covers
   target atoms in the requested representation also covers atoms outside the target. Each of
   its items outside the target counts as spill, whatever its colour, so the score falls the
   more atoms are covered. Example: the whole chain as yellow spacefill spheres when one
   residue was asked for. The requested representation drawn outside the target in a
   separate style, for example red spacefill spheres on the neighbours beside the yellow
   spacefill spheres on the residue, is not spill; it falls under rule 3.
2. *Extra on the target.* The answer adds another representation that covers only target
   atoms. Each of its items counts as extra. Example: ball-and-stick on the residue as well
   as the requested spacefill spheres.
3. *Unrequested context.* Any other style that reaches beyond the target, such as a cartoon or
   a surface of the chain, or ball-and-stick on the residue and its neighbours, is ignored,
   however far it reaches and whatever its colour, on the target atoms as well as outside
   them. It is ignored even where a surface would hide the target in a real picture; F1 and
   task success count it.

*Target recall* is credit divided by wanted. *Target precision* is credit divided by the sum
of attempted, spill and extra. The target score is the harmonic mean of the two. Where the
reference draws the target in more than one way, for example two residues in different
colours, or a residue with a text label, recall and precision are computed for each part and
averaged before the harmonic mean is taken (SI Section S4.3).

Rule 2 by hand, for the running example (Table 3, row S9). The target has
24 atoms and one requested style, so wanted is 24. The
answer draws that style on all of them: credit 24, attempted
24. Its added ball-and-stick is confined to the residue: extra
24. Target recall is 1, target precision is
24/48 = 0.50,
and the target score is 0.67. The caption of Table 3 works rule 1 in
the same way.

The line between rules 2 and 3 is whether the added style is confined to the target. A second
representation on the target alone is read as another answer to "how should these atoms be
drawn?", and a style that also covers other atoms as background. The line is a convention,
and it has a cost that two rows of Table 3 show: ball-and-stick added to the residue alone
is penalised (row S9, 0.67), and the same
ball-and-stick added to the residue and its two neighbours is not (row
S10, 1.00). Task success and F1
penalise both.

An answer is *target-right* when its target score is exactly 1: the requested style is on the
target atoms and on no others, and nothing else is confined to them. The target score
separates "found the wrong residue" from "found the right residue and added context". Table 3
gives the score of one example of each rule.

On the call-list track the same counts are made on the changes from the default view on the
target atoms: a style that a call adds, or a default style that it removes. Every first
request of this track asks for some change on its target, so a load with no further call is
target-right in none of the 372 first requests (checked with the
grader). A paired request for a cartoon is no exception ("Load 1EHZ and show the RNA as a salmon cartoon."): the
default view already draws a cartoon, but not in the requested colour, and the reference
recolours it.

A target score exists for 766 of the 797 tasks. For
733 of them the generator stores the target. For
33 more, in which a first request changes a setting of the
viewer or hides something (a background colour, the water molecules), the target is
everything the reference changes. The remaining 31 tasks
are follow-up turns whose edit takes something away, changes or restores a setting of the
whole view, or needs no change. They have no target score, and averages leave them out:
after such an edit no atoms are left that are "drawn as asked", and with everything the
reference draws as the target, the start state returned unchanged would earn nearly full
marks.

**Unrequested context: the rule on each track.** On the scene track the screen starts empty,
so anything drawn beyond the request counts against precision and task success. On the
call-list track the viewer starts with the whole structure drawn, only changes from that
default view are graded, and leaving the default view in place costs nothing. Task success is
therefore not the same test on the two tracks. The target score ignores unrequested context
on both tracks and is computed with the same counts on both; the more generous rule of the
call-list F1 (one half for any change to the right atoms) is not used for it. The verdict
*target-right* is therefore the same test on both tracks. Two consequences follow, and they
fix the primary score of each table (Box 2). Within a track, models are ranked by the task
success rate, and the target score is reported beside it. Between the two formats, models
are compared on the pairs only, and first on whether each answer is target-right (Section
5.4).

When a task lists several accepted answers (Section 3.3), an answer is graded against each,
and the best result counts.

### 4.3 The running example, graded

Figure 4 and Table 3 grade several answers to the running example. The reference draws
Trp64 of chain X as yellow spacefill spheres, and
nothing else.

![**Figure 4. Drawn-state grading of the reference and two answers to the running example.** Top: the three drawings as Mol\* 5.9.0 renders them, all from one camera. The reference and Answer A look equally plausible: each is one residue as yellow spheres, and nothing in either picture says which residue it is. Below, each panel shows a stretch of chain X in author numbering, the facts of the drawn state, and the scores. *Fact*: all atoms that are drawn in the same way. *Recall*: for each fact of the reference, the fraction that the answer also draws, averaged over those facts. *Precision*: the same for the facts of the answer. *F1*: the harmonic mean of recall and precision. *Task success*: drawn state exactly right. *Target score*: how far the requested style is on the requested atoms and on no others (0 to 1); unrequested background, such as the cartoon of Answer B, is ignored.](generated/fig_grading.svg)

**Table 3. Answers to the running example and their scores**, computed by the benchmark's
grader. Rows S1 to S10 are scenes, rows C1 to C7 call lists. *F1*: how much of the drawn state
is right (0 to 1). *Task success*: the drawn state is exactly right. *Target score*: how far
the requested style is on the requested atoms and on no others (0 to 1; exactly 1 is
*target-right*); unrequested background, such as a cartoon of the protein, is ignored. *Spill*, *extra on the target* and *context* are the three rules for extra
drawing of Section 4.2. In the two spill rows the target score can be checked by hand, in
items (one style on one atom). The target has 24 atoms, so credit and
attempted are both 24. The answer draws the yellow spacefill spheres on
56 atoms in all (row S7) or on all
2,691 atom records of the author chain (row S8); the
items outside the target are spill. Target precision is therefore
24/56 = 0.43 or
24/2,691 = 0.009,
target recall is 1, and their harmonic mean is 0.60 or
0.02. On the call-list track the cartoon of the default view is
on screen in every row but row C7 and costs nothing; on the scene
track the same cartoon is unrequested context (row S5).

| Row | Answer | F1 | Task success | Target score |
|:--|:------------------------------------------|--:|:--|--:|
| | **Scene track** | | | |
| S1 | Reference: author chain X, author residue 64, yellow spacefill spheres | 1.00 | yes | 1.00 |
| S2 | The same residue named by label numbering (label chain A, residue 64) | 1.00 | yes | 1.00 |
| S3 | Number copied from the variant name and used as the author number (Ser82) | 0.00 | no | 0.00 |
| S4 | Right residue, drawn red | 0.50 | no | 0.50 |
| S5 | Right residue, plus a grey cartoon of the protein that the request does not ask for: context | 0.40 | no | 1.00 |
| S6 | Wrong residue, plus the grey cartoon | 0.00 | no | 0.00 |
| S7 | Right residue, and the same yellow spacefill spheres on its two neighbours (residues 63 to 65): spill | 0.60 | no | 0.60 |
| S8 | The whole chain as yellow spacefill spheres: spill | 0.02 | no | 0.02 |
| S9 | Right residue, plus ball-and-stick on the same residue alone: extra on the target | 0.67 | no | 0.67 |
| S10 | Right residue, plus ball-and-stick on residues 63 to 65: context | 0.40 | no | 1.00 |
| | **Call-list track** | | | |
| C1 | Reference: UniProt P61626 position 82, resolved by the viewer; the cartoon of the default view is left as it is | 1.00 | yes | 1.00 |
| C2 | The same residue named by author numbering (chain X, residue 64) | 1.00 | yes | 1.00 |
| C3 | Number copied from the variant name and used as the author number (Ser82) | 0.00 | no | 0.00 |
| C4 | Right residue, drawn red | 0.50 | no | 0.50 |
| C5 | Load only, no further call | 0.00 | no | 0.00 |
| C6 | Right residue; its segment of the default cartoon is recoloured too (an accepted answer, Section 3.2) | 1.00 | yes | 1.00 |
| C7 | Right residue, and the default cartoon hidden, which the request does not ask for | 0.33 | no | 1.00 |

Four points follow. First, an answer may name the residue in any numbering: rows
S2 and C2 are written differently from the reference and
score the same, because they draw the same atoms. Second, the answer that copies the "82" of
p.W82R (rows S3 and C3) draws
Ser82, shares no atom with the reference, and
receives 0 on all three scores. Third, the answer that finds the right
residue and adds a grey cartoon of the protein (row S5) has a target score of
1.00 but an F1 of 0.40 and no task success: it
drew a cartoon over the whole chain that the request did not mention. Fourth, the last two
rows show what is special to the call-list track. A call list that also recolours the
residue's own segment of the default cartoon passes because the task lists that drawn state
as a second accepted answer, not because of the F1 rule (row
C6; Section 3.2). A call list that hides the default cartoon makes
a change that the request does not ask for: it is target-right but not a task success (row
C7).

The F1 of the answer with the added cartoon (Table 3, row S5; Figure 4,
Answer B) is worked out as follows. The answer has two facts. Fact 1 is the atoms of
Trp64; they carry two styles, the grey cartoon and the
yellow spacefill spheres, and the reference has one of the two: one half. Fact 2 is all other
atoms of the protein; they carry only the grey cartoon, and the reference has none of it:
zero. Precision is the mean of the two, 0.25. Recall is
1.00, because the reference's one fact is fully present. F1, their
harmonic mean, is 0.40.

Row C7 is worked out by the call-list rule of Section 4.2. The
reference has one fact, the atoms of the residue. The answer has two: the residue, and all
other atoms, on which it hid the cartoon. Reference and answer both changed the residue, but
it ends up drawn differently, because the answer also removed its cartoon: one half. Only the
answer changed the other atoms: zero. Recall is 0.50, precision
is the mean of one half and zero, 0.25, and F1 is
0.33. The target score stays at 1.00:
the yellow spacefill spheres are on the residue and on no other atom, and hiding the cartoon
is a change that reaches beyond the target, which rule 3 ignores.

An F1 of 0.40 alone does not say what went wrong: a half-right residue
with no context could score in the same range (the right residue drawn red scores
0.50, row S4). The target score of 1.00 says that the
residue is right and that the loss is unrequested context.

### 4.4 Valid, unshowable and schema-breaking answers

Every answer gets one *outcome*. It is *valid*, or it is *invalid* in one of two ways that must
be kept apart: unshowable, or schema-breaking.

- **Valid.** Scene track: the answer parses as JSON, is a scene, is accepted by the
  validation of Mol\* 5.9.0 itself, run without a display, and names a structure file that
  the viewer can load. The grader decides the last point from the address alone, without
  fetching anything: the address must be that of a structure file on a site of the PDB
  archive or of the AlphaFold Protein Structure Database, in the file format that the scene
  says it parses. Call-list track: the answer parses as a JSON list that fits the *call
  schema*: every call is one that the format guide lists, and every field has the documented
  type.
- **Unshowable** (both tracks). The answer contains no parseable JSON of the right outer shape
  or, on the scene track, is not a scene, is rejected by Mol\*, or is well formed but names a
  file that the viewer cannot load (a web page in place of a structure file, for example).
  Nothing can be shown, and the answer scores 0 on all three scores. A scene that loads a
  readable file of an entry that the task does not accept is a different case: it is valid,
  and it scores 0 because nothing can be compared (Section 4.1).
- **Schema-breaking** (call-list track only). The answer parses as a JSON list but holds an
  unknown call or a wrongly typed field. The viewer ignores such parts and carries on, and so
  does the grader: the list is replayed as the viewer would treat it and keeps the scores it
  earns. It is not counted as valid.

An answer that the provider cut off at the token limit gets the outcome of the text that
arrived, which is usually unshowable; the outcome tables count cut-off answers apart from
other invalid ones. SI Table S5 lists every outcome with its score.

Scores are averaged in three named ways.

- **Strict** (the default): every answer counts. An unshowable answer scores 0; a schema-breaking
  call list keeps the scores it earns. This is what a user of a bare model, one without
  tools, would experience.
- **Valid-only**: the mean over a model's valid answers, all pooled, so a task with more
  valid answers weighs more and a task with none contributes nothing. This separates "wrote a
  loadable answer" from "the answer is right".
- **Repaired**: a counterfactual. Each answer that is not parseable JSON is passed through an
  offline JSON repair library [35] and graded again. No model is called. The repaired
  score is reported beside the strict score and never replaces it.

### 4.5 How well the grader itself works

A grader that compares drawn states can still be wrong: it may reject a correct answer that is
written in an unexpected way, or pass a wrong one. We test this with a *control set* of
2,175 controls (Table 4). A control is a reference and one answer whose verdict is
known from how the answer was made. The answer is one of three things.

- **Identical**: the reference itself. It must pass.
- **Equivalent**: the reference rewritten so that the viewer shows the same. Examples: a
  residue range as a list of residues; label numbering in place of author numbering where the
  two name the same atoms; a colour as a hexadecimal code; the same atoms selected as one
  component or as several; on the
  call-list track, a wrong step that a later step undoes. It must pass.
- **Wrong**: an answer that shows something else. Examples: the neighbouring residue; the other
  chain; the UniProt number used as the author number on a structure where they differ; a
  named shade of the colour that lies outside the colour tolerance (Section 4.6); a drawn part
  that is missing or added; another copy of the ligand. It must fail.

A *false pass* is a wrong answer graded as a task success. A *false fail* is an identical or
equivalent answer graded as not a success.

The grader makes no error on the control set, and this must be read with care. We developed
the grader against the controls and corrected it until it agreed with every one. The zeros
therefore show that the stated rules are implemented and stay implemented: the control set is
run as a test on every change. They are not an estimate of how often a way of writing an
answer that we did not foresee is misjudged. Finding such cases needs people, and is the
purpose of the rating study (Section 5.5).

**Table 4. Error rate of the grader on the control set.** *False pass*: wrong answers graded as
task success, out of all wrong answers. *False fail*: identical or equivalent answers graded as
not a success, out of all such answers. *Earlier grader*: our own grader that this work
replaces on each track (for the scene track, a comparison of scene trees path by path; for the
call-list track, a comparison of call sequences field by field), with a score of exactly 1
read as success. *Structures*: the scene controls use all 78 structures
that tasks use. The call-list controls are built around a protein residue, so they use
74 of these 78, predicted structures
included: the other 4 entries
(1BNA, 1EHZ, 1KF1 and 1Y26) hold only DNA or RNA. Of the controls,
910 on the scene track and 150 on the
call-list track (267 of their 300
call lists) were also checked in the running viewers (see the text below the table).

| Track | Controls | Structures | Kinds of equivalent / wrong answer | False pass | False fail | Earlier grader: false pass | Earlier grader: false fail |
|:---|---:|---:|---:|---:|---:|---:|---:|
| Scene | 1,155 | 78 | 25 / 26 | 0 of 505 | 0 of 650 | 16 of 505 (3%) | 284 of 650 (44%) |
| Call list | 1020 | 74 | 22 / 23 | 0 of 445 | 0 of 575 | 95 of 445 (21%) | 319 of 575 (55%) |

**The check in the running viewers.** The verdict of a control comes from how it was made,
not from the grader. For many controls it was also checked in the viewers; this is the same
check that compares the atom tables with the viewer (Section 3.7).

- *Scene track.* Both scenes of 910 of the
  1,155 controls were loaded in Mol\* 5.9.0, run without a display,
  and their drawing was read back. In every one the viewer showed the same drawing where the
  control must pass and a different one where it must fail, and the grader's resolved atoms
  were those that the viewer drew.
- *Call-list track.* A sample of 150 controls, with every kind of
  control represented, was replayed in PDBe Mol\* 3.3.2: 267 of
  their 300 call lists. Each selection was compared atom for
  atom, and every list ended in the state that the grader computes.
- *Default view.* The default view after a load with no further call was compared in the
  same way for 73 of the 74 PDB entries of the
  panel.

Not checked in a viewer are 245 scene controls of kinds that
cannot be read back in this way (for example the text of a label), any control
added after the read-back, the call-list controls outside the sample, and every call list
that selects by UniProt number. SI Section S5 gives the counts and says how the sample was
drawn.

The earlier graders, both our own, give the scale of the problem that the control set
detects (Table 4, last two columns). SI Section S5 lists every kind of control with its
counts.

### 4.6 What is deliberately not graded

Camera coordinates are never graded. A requested focus is graded by which residues the camera
frames; an unrequested focus in the answer is ignored. Sizes, line widths and the appearance of
labels are not graded. Two opacities count as the same if they differ by at most
0.05. Two colours count as the same if their red, green and blue values
(0 to 255) each differ by at most 32. Requests use a palette of
19 named colours, of which the two closest are
55 apart, so no palette colour can pass for another. A named
lighter or darker shade of a requested colour, such as "darkred" for red, lies outside the
tolerance and counts as wrong. In the pilot run the tolerance decided no case (SI Section
S4.5).

## 5. Experimental setup

One run fills every result in Sections 6.1 to 6.5. Its plan is fixed in a single manifest file
before any model is called: the corpus version and its hash, the models and their prices, the
prompting conditions, the number of answers per task and the limits. SI Section S6 reproduces
it.

### 5.1 Models

The models are chosen by a written rule, not by results. The *core models* are the
16 language models in the results that we published online in October 2026
(the results browser of Section 12). They are kept unchanged, so that the choice of models
depends on no result of the present benchmark. Most are the smaller, cheaper models of
their providers; list prices run from 0.18 to
9 US dollars per million output tokens. Of the
16, 13 have *open weights* (the weights of the model can
be downloaded) and 3 have *closed weights* (the model can be used only
through a provider's service).

- Closed weights (3): claude-haiku-4-5 (Anthropic), gemini-3.5-flash (Google), gpt-5.4-nano (OpenAI).
- Open weights (13): deepseek-v3.2 (DeepSeek), deepseek-v4-flash (DeepSeek), gemma-3-27b-it (Google), llama-4-maverick (Meta), minimax-m3 (MiniMax), mistral-small-2603 (Mistral AI), kimi-k2.6 (Moonshot AI), nemotron-3-super-120b-a12b (NVIDIA), gpt-oss-120b (OpenAI), gpt-oss-20b (OpenAI), qwen3-30b-a3b-instruct-2507 (Alibaba), qwen3-next-80b-a3b-instruct (Alibaba), glm-5.2 (Z.ai).

SI Table S7 lists every model with its full identifier and price. All but one of the core
models ran in the October pilot of the
scene track (Section 6.6); the exception, mistral-small-2603, could not be reached on
that day and had earlier call-list results only.

Up to 5 *optional models* are the largest models of their kind
(list prices from 4.44 to
20 US dollars per million output tokens): the largest
current model of several providers of closed-weight models, and the largest model with open
weights, as listed on the day the prices were recorded
in the manifest (22 November 2026). The manifest names them. Which of them
are run is decided before any result exists, from the projected cost alone, and they are
marked † in the tables. No model is added or dropped after results are seen.
⟦PENDING: Dan — which of the optional models are run⟧

Two scripts that use no model are run on both tracks as floors. The *keyword script* maps
words in the request to fixed answers by rule. The *literal script* writes what the request
spells out: the entry, chains, residue numbers, compound codes, colours and representations
that it names, with every number used as written, as an author residue number. It looks
nothing up, so it is right where the request states everything in the structure's own
numbering and wrong wherever something must be found. The difference between a model and
the literal script is what the model adds to the words of the request.

### 5.2 Prompting conditions

Table 5 lists the four prompting conditions. In each of them a model receives a system prompt
and the request, and returns one answer. A model cannot
look anything up, cannot ask a clarifying question, and does not see a rendered result. It is not
given the structure file. Both system prompts tell the model that its answer is judged by what
the viewer ends up showing; the scene prompt adds that anything drawn that was not asked for
counts against the answer.

**Table 5. Prompting conditions.** *Main* is the condition from which all main results come.
*Format guide*: a frozen text in the system prompt that documents the answer format. *JSON
mode*: a provider option that forces syntactically valid JSON. *Grounding pack*: the result of
an offline lookup, appended to the request: the chains of the structure, its residue ranges in
both numberings, the UniProt mapping and, for a clinical task, the residue that each named
variant maps to. *Answers per task*: answers of each model to each task.

| Condition | What the model is given | Run on | Answers per task |
|:-----|:----------|:----------|--:|
| **Main** | A short instruction, the rule for the answer ("answer with one JSON value and nothing else") and the format guide | all models, all tasks, both tracks | 3 |
| Main + JSON mode | The same, with JSON mode switched on | every model that offers JSON mode: 15 of the 16 core models (all but claude-haiku-4-5) and each optional model that is run; all tasks, both tracks | 1 |
| Main + grounding pack | The same, with the task's grounding pack appended to the request | all models; the lookup categories (name resolution, clinical variant), scene track | 3 |
| No format guide | The instruction and the rule for the answer only | 3 models (claude-haiku-4-5, deepseek-v3.2, qwen3-30b-a3b-instruct-2507), the same as in the pilot run; all tasks of the scene track | 3 |

A grounding pack never contains a scene, a colour or a representation. But for a clinical
task it contains the mapped residue, and for a name-resolution task a list of entries. The
condition with a grounding pack therefore shows the most that a perfect lookup tool could add:
the lookup has been done and its result handed over. It is not a test of whether a model can
use raw lookup tables. For the running example the pack states that UniProt
19–148 are author residues
1–130 of chain X, and that
p.W82R is author residue 64 of that chain (SI Section S1).

The grounding-pack condition is run on the scene track only. Name resolution exists only
there, and on the call-list track a clinical request can be answered with the UniProt
selector, without the residue number that the pack supplies (Section 3.4).

**What the format guide contains.** The format guide is all that the model is told about the
answer format, so its content matters. The guide of the scene track (1,087
words) lists the kinds of node of a scene and the fields of a selection, among them the chain
and residue number in author numbering and in label numbering. The guide of the call-list
track (1,253 words) lists the calls and their fields, among them
selection by author numbering, by label numbering and by UniProt accession and position.
Neither guide says how a given structure is numbered, and the scene guide does not mention
UniProt. With the instruction and the rule for the answer, the system prompt has
1,328 words on the scene track and 1,556 on the call-list
track. SI Section S7 prints both system prompts and both guides in full.

No prompt was tuned on benchmark tasks. Each of the two system prompts has one worked example,
and both examples use entry 1HSG, which no task uses. The format guide of the scene track also contains one short illustration of a
distance line on an entry that tasks do use; no task asks for that distance.

### 5.3 Sampling

Each model answers each task three times in the main condition, at the provider's
default temperature. The limit on the length of an answer is 8,000 tokens.
Of the core models, seven first write reasoning text that the user does not
see; the provider bills it and counts it against the limit. For these models the limit is
16,000 tokens for reasoning and answer together (SI Table S7). An
invalid answer is scored as it stands and is not retried; only transport errors are retried.
Every raw answer is archived with its token counts, the reason the provider gives for the end
of the answer, and its cost.

### 5.4 Statistics

- **Per-model scores** are means over tasks of the mean over the task's 3
  answers. For task success this is the task success rate; the all-3 rate (the
  share of tasks on which all 3 answers succeed) is reported beside it (Section
  4.2). Valid-only scores are the exception: they pool a model's valid answers (Section 4.4).
  Means over models are means over the core models and the optional models that were run;
  they leave the two scripts out.
- **Intervals** are 95% bootstrap intervals [36] with 10,000
  resamples.
    - *What is resampled.* Whole structures, with replacement, not single tasks, because
      tasks on one structure share its difficulties. Each task goes with the structure of its
      reference. The table of results by category (Section 6.2) gives the number of structures
      beside the number of tasks.
    - *What is not.* The 3 answers to a task are averaged before resampling and
      are not themselves resampled, so an interval reflects the choice of structures and
      tasks, not the variation between a model's answers to one task. Models are treated as
      fixed: an interval on a mean over models describes these models, not models in general.
    - *Valid-only scores.* Structures are resampled with all the valid answers to their
      tasks, and the pooled mean is recomputed in each resample.
    - *Differences.* Where the same tasks are compared under two conditions or two wordings
      (planned comparisons 2 to 6 below), the difference is taken task by task, and
      structures are resampled with the differences of their tasks. In comparison 1 the two
      splits share no structure, and each split is resampled on its own. In comparison 7 the
      two groups of clinical tasks can share a structure; each resample draws the structures
      once, and both groups are recomputed on that draw.
    - *A limit.* In the clinical category, several structures can belong to one protein. They
      are resampled as separate structures (Section 9.4).
- **Paired comparison of formats**, in six parts.
    - *Unit.* For each model and pair, a side is right when at least 2 of its
      3 answers are right (the majority summary of Section 4.2). The test
      below needs one yes-or-no verdict per side, and the majority depends less on a single
      unlucky answer than the first answer alone would.
    - *Primary comparison.* An answer is right when it is target-right, that is, when its
      target score is exactly 1. This is the same test in both formats. It uses the
      250 pairs that have a target score. The other
      8 pairs are follow-up turns without one (Section 4.2):
      their edit hides the water (2), sets the background
      colour (2) or needs no change
      (4).
    - *Secondary comparison.* An answer is right when it is a task success. This is not the
      same test in the two formats (Section 4.2). It uses all 258 pairs
      and is shown beside the first.
    - *Unshowable answers* count as not right, so a pair that is right on one side only can
      reflect an answer that could not be shown as well as one that selected the wrong
      atoms. The one-sided counts must be read against the share of unshowable answers per
      model and track (SI Section S9).
    - *Test.* The two counts of pairs that are right on one side only are compared with
      McNemar's exact test [37]. We report the four counts for every model. The
      test treats pairs as independent, although several pairs sit on one structure, so its p
      values are somewhat too small. We read them as descriptions, and we give beside them
      the difference between the two one-sided counts as a share of the pairs, with a 95%
      interval for which structures are resampled.
    - *Repeats.* The analysis is repeated without the 15
      pairs whose reference call list switches off part of the default view (Section 3.4),
      and without the clinical pairs, in which the call-list viewer can do the mapping
      itself. The first set holds first requests only and the pairs without a target score
      are follow-up turns, so the two sets do not overlap.
- **The central clinical comparison (planned comparison 7).** It carries the question of the
  Introduction. Clinical tasks of the scene track in which copying the number in the variant
  name is right are compared with those in which it is wrong. The primary score is the
  target score, because task success also falls when an answer adds unrequested context; the
  difference in task success rate is given beside it. The result is the difference row of
  Table 10, with an interval. The grouping by offset is reported for description only.
- **Six further planned comparisons (Table 12).** Each is a difference in task success rate
  with an interval.
    1. Tasks on the other structures against the set-aside split (both tracks).
    2. Full against terse wording (both tracks).
    3. Full against indirect wording (both tracks).
    4. With and without JSON mode (both tracks). The single JSON-mode answer to a task is
       set against the mean of its 3 answers in the main condition.
    5. With and without grounding pack (scene track).
    6. With and without format guide (scene track).
- **Not compared: the totals of the two tracks.** The tracks differ in their mix of
  categories and in the length of the answer, so the formats are compared on the pairs only.
- **What F1 is read against.** F1 has a floor that needs no skill: a scene with nothing but a
  protein cartoon, or a follow-up's start state returned unchanged, shares most of its drawing
  with the reference. Within a track the task success rate is therefore the primary score
  and the target score is reported beside it; F1 is shown with the two scripts beside it, which mark
  that floor.

The McNemar tests are one per model; we read each as a description of that model and not as a
family of tests. We do not correct for multiple comparisons, and we report every count.

### 5.5 Human check of the grader

The grader's verdict is also checked against people. After the run, volunteers will see
*picture comparisons*. One picture comparison shows the request and four pictures: the
reference and a model answer, each drawn whole and each drawn again zoomed on the target
atoms. The reference and the answer are always rendered from the same camera, that of the
reference, so a difference between two pictures is a difference between the scenes. For a
follow-up task the start scene is shown as well. A rater gives two verdicts on each picture
comparison, each of them "same", "different" or "can't tell":

- *On the whole scenes:* judged against the request, does the answer show the same thing as
  the reference? This verdict is compared with the grader's task success.
- *On the zoomed pictures:* is the requested part picked out in the same way? This verdict is
  compared with a target score of 1.

A task without target atoms is shown whole only, and receives the first verdict only.

*The sample.* The study has 300 picture comparisons. Each is of a valid
scene-track answer of the main condition. Tasks of the name-resolution category are left
out, because their requests accept any sensible view, so "the same picture" is not the
question. The call-list track is left out because we cannot yet picture its answers zoomed
on the target; its grader rests on the control set and on the replay in the viewer (Section
4.5). The sample is drawn in three groups of 100 by the grader's verdict:
answers that it counts as a task success; answers that it does not count as a success
although their target score is 1; and the other answers that it does not count as a success.
The sample obeys four further limits:

- no task supplies more than 2 answers, and never more than
  1 from the same model;
- within each group, the categories contribute as nearly equal numbers of answers as the
  available answers allow;
- no model supplies more than 12% of the set;
- among the task successes, answers whose pictures differ from those of the reference are
  taken first, up to 75% of the group, because a picture identical to
  that of the reference tests nothing.

Each picture comparison is rated by two raters. A rater sees
35 items: 27 picture comparisons,
6 comparisons whose verdict is known from how they were made, and
two of the rater's own earlier comparisons shown again. A rater who
fails the comparisons of known verdict, by a rule fixed before the study, is reported and
left out of the primary analysis.

We will report four things, with intervals:

1. the share of the grader's task successes that people call the same, which bounds its
   false passes;
2. the share of the answers it does not count as a success that people call different, which
   bounds its false fails, for the two such groups separately;
3. the same two shares for a target score of 1 against the verdict on the zoomed pictures;
4. the agreement between raters, as the yardstick for the agreement between people and the
   grader.

The record of the sample holds the number of answers of the run in each category and
verdict, and the shares are weighted back to the run with it. Every answer on which all its
raters contradict the grader will be listed. Such a case is either an error of the grader or
a difference that the picture does not show.

An *image judge* is a vision-language model that is shown the same pictures and asked the
same questions. It contributes to no score in this paper. If it is run on the pictures of
the study, its agreement with people is reported as a secondary result.

A smaller trial of the study has been run on the pilot answers (Section 6.6, Finding 6).

### 5.6 Reproducibility

One command performs the run from the manifest. It does not start if the projected cost is
above a cap in US dollars that the manifest states, and it stops if spending would pass it.
One command rebuilds every table, figure and number in this paper from the archived answers.
A rehearsal with a mock model exercises the whole path at no cost. Grading needs no network
access and no paid service.

## 6. Results

MolBench has had two versions, and this paper names them in one way throughout. The *first
version* is the benchmark as it was public from May 2026 until the present corpus replaced
it. At the time of its last run it had a corpus of 70 scene
tasks on 14 structures, 20 hand-written call-list
tasks, and two graders that compared text (Section 4.5). Two of its runs are used in this
paper: one of the call-list tasks in July 2026, and one of the scene tasks in October 2026,
which we call the *pilot run*. The *present version* is the benchmark of Sections 3 and 4.

The only results that exist today come from the first version. They are kept apart from
everything else, in the box of Section 6.6. The path to a provider has also been tried on a
few tasks of the present version; this *provider pilot* is not a result, and its one table
is in SI Section S6.1. Sections 6.1 to 6.5 show the tables that the
final run will fill: their layout, captions and definitions are fixed, and the cells are
filled by script from the archive of the run. Figure 5 shows the layout of the result figure.
In this draft the tables with one row per model (Tables 6, 9a and 9b) show their first rows
only, and Table 7 is described but not drawn.

![**Figure 5. Layout of the result figure that the final run will fill (no data shown).** **A**: task success rate (the share of answers whose drawn state is exactly right) per model, strict, with 95% intervals, one plot per track. The two plots must not be compared with each other (Section 4.2); formats are compared in panel B only. **B**: for each model, its 250 pairs that have a target score, by which side was right (at least 2 of its 3 answers target-right, that is, with a target score of exactly 1: the requested style on the requested atoms and on no others). **C**: valid answers only, so that the panel shows what is lost after an answer could be shown: task success rate and target score (how far the requested style is on the requested atoms and on no others; unrequested background is ignored) per category. A target score well above the task success rate means that the requested atoms were right and something else was not. Panel A is strict and panel C is valid-only, so the two must not be compared.](generated/fig_result_shapes.svg)

### 6.1 Models on both tracks

**Table 6. Scene track, main condition.** One row per model; † marks an optional model.
*Weights*: open if the weights of the model can be downloaded, closed if the model can be
used only through a provider's service. *Valid answers*: share of answers that parse and that
the viewer accepts. *Task success rate*: share of answers whose drawn state is exactly right.
*Target score*: how far the requested style is on the requested atoms and on no others (0 to
1; exactly 1 is *target-right*); unrequested background, such as a cartoon of the protein, is
ignored. *F1*: how much of the drawn state is right (0 to 1).
*Strict*: every answer counts, and an unshowable answer scores 0. *Valid-only*: the mean over
the model's valid answers, pooled. *All-3 rate*: share of tasks on which all
3 answers are exactly right. *Cost*: US dollars for all calls of the model in
this condition, at list price. Intervals (95%, structures resampled; Section 5.4) will be
given with each score. F1 valid-only is in the SI.

| Model | Weights | Valid answers | Task success rate, strict | Target score, strict | F1, strict | Task success rate, valid-only | Target score, valid-only | All-3 rate | Cost (USD) |
|:-------|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| Keyword script (no model) | – | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Literal script (no model) | – | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| claude-haiku-4-5 | closed | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| … 15 further rows for the other core models and up to 5 for the optional models (SI Table S7) | | ⟦PENDING: final run⟧ | | | | | | | |

**Table 7. Call-list track, main condition.** Same columns and definitions as Table 6, except
that a *valid answer* is a JSON list that fits the call schema, and a schema-breaking call list
keeps, under *strict*, the scores it earns when replayed (Section 4.4).

⟦PENDING: final run — the table for the call-list track, in the shape of Table 6⟧

### 6.2 Categories

**Table 8. Scores by category and track**, mean over the models (the two scripts are left
out). *Structures*: the number of structures that the tasks of the row sit on, which is the
number of units resampled for its intervals. *Task success rate*, *target score* and *F1* as
in Table 6. *Strict*: every answer counts, and an unshowable answer scores 0. *Valid-only*:
the mean over valid answers, which shows the difficulty of a category once the format has been
written correctly. The two rows marked *of which* divide the answers of the name-resolution
category by the entry that the model chose; they are sets of answers, so they have no number
of tasks. Answers on the reference entry are graded on drawn state; answers on another
accepted entry are, with few exceptions, compared with the reference as written (the weaker
rule of Section 4.1).

| Category | Tasks | Structures | Task success rate, strict | Target score, strict | F1, strict | Task success rate, valid-only | Target score, valid-only |
|:------------------------|---:|---:|---:|---:|---:|---:|---:|
| **Scene track** | | | | | | | |
| Translation | 73 | 67 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Structure-grounded | 63 | 55 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Name resolution | 39 | 39 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
|  *of which:* answers on the reference entry | – | – | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
|  *of which:* answers on another entry that the task accepts (graded by the weaker rule of Section 4.1) | – | – | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Clinical variant | 82 | 31 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Interactions | 40 | 38 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Follow-up turn | 58 | 42 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Several right answers | 26 | 23 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| **Call-list track** | | | | | | | |
| Translation | 178 | 73 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Structure-grounded | 63 | 55 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Clinical variant | 82 | 31 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Follow-up turn | 44 | 41 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Several right answers | 15 | 12 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Viewer settings | 34 | 34 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |

### 6.3 The same request in two formats

**Table 9. Paired comparison of the two formats.** For each model, its pairs (one request on
both tracks, same target atoms) are divided into four cells, in two tables. A side of a pair
is *right* when at least 2 of its 3 answers are right. *Table 9a* (primary): an
answer is right when it is target-right, that is, its target score is exactly 1: the
requested style is on the requested atoms and on no others, and unrequested background is
ignored. This is the same test in both formats. Table 9a covers the
250 pairs that have a target score; the other
8, all follow-up pairs, have none (Sections 4.2 and 5.4) and
appear in Table 9b only. *Table 9b* (secondary): an answer is right
when it is a task success, that is, its whole drawn state is exactly right; this is not the
same test in the two formats (Section 4.2). Table 9b covers all 258
pairs. An unshowable answer is not right. The four count columns give the number of pairs right
on both sides, on one side only, or on neither. *McNemar p*: exact test that the two one-sided
counts are equal; a small value means that one format is harder for this model. The test
treats pairs as independent (Section 5.4). *Difference*: the number of pairs right in the
scene only minus the number right in the call list only, as a share of the pairs, with a 95%
interval (structures resampled). † marks an optional model.

**Table 9a. Primary comparison. A side is right when at least 2 of its 3 answers are target-right. The 250 pairs that have a target score.**

| Model | Pairs | Right on both sides | Right in the scene only | Right in the call list only | Right on neither side | McNemar p | Difference: scene only minus call list only, as a share of the pairs (95% interval) |
|:--------|--:|---:|---:|---:|---:|---:|---:|
| claude-haiku-4-5 | 250 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| deepseek-v3.2 | 250 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| … up to 19 further rows, one per model | | ⟦PENDING: final run⟧ | | | | | |

**Table 9b. Secondary comparison. A side is right when at least 2 of its 3 answers are task successes. All 258 pairs.**

| Model | Pairs | Right on both sides | Right in the scene only | Right in the call list only | Right on neither side | McNemar p | Difference: scene only minus call list only, as a share of the pairs (95% interval) |
|:--------|--:|---:|---:|---:|---:|---:|---:|
| claude-haiku-4-5 | 258 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| deepseek-v3.2 | 258 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| … up to 19 further rows, one per model | | ⟦PENDING: final run⟧ | | | | | |

Where both formats demand the same knowledge, which is every category with pairs except the
clinical one, a pair that is target-right on one side only points to the format, and a pair
that is wrong on both sides is a candidate for an error of content. Clinical pairs must be
read differently. There a right call list does not show that the model knew the residue,
because the viewer can do the mapping (Section 3.4); "call list right, scene wrong" then
points to the mapping, not to the scene format. The counts without the clinical pairs are
the cleaner test of the formats.
⟦PENDING: final run — the same counts without the clinical pairs, and without the 15 pairs whose reference call list switches off part of the default view (Section 3.4); and, in the SI, the one-sided pairs divided by whether the side that was not right was unshowable⟧

### 6.4 Clinical variants

**Table 10. Clinical tasks on the scene track, grouped by whether copying the number is
right.** On this track the model must map the number itself. *Target score* (how far the
requested style is on the requested residue and on no other atoms, with unrequested
background ignored; 0 to 1; the primary score of this table) and *task success rate* (drawn
state exactly right), strict, mean over the models; SI Section S9 will give the first two
rows for each model. *With grounding pack*: the result of the
lookup, including the mapped residue, is appended to the request. The rows are two
groupings of the same 82 tasks (Section 3.3.1, Table 2a). *Copying the number*: an
answer that uses the number printed in the variant name as the author residue number is right,
or wrong. *Offset*: the author number of the target residue differs from its UniProt number,
or does not. The *difference* row is planned comparison 7 of Section 5.4. *Matched tasks*:
the same variant, named in UniProt numbering, asked on a structure with an offset and on a
predicted structure without one (7 sets; descriptive
only; Section 3.3.1). In the helix and strand tasks the model
must also know where the entry records that helix or strand to begin and end; they are a
subset of the 82 and are also reported apart.

| Clinical tasks (scene track) | Tasks | Target score (the primary score here) | Task success rate | Target score with grounding pack | Task success rate with grounding pack |
|:------------------|--:|---:|---:|---:|---:|
| **Copying the number**: copying is right | 34 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| **Copying the number**: copying is wrong | 48 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Difference between these two rows (95% interval) | | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| **Offset** (for description only): no offset | 23 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| **Offset**: offset | 59 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Matched tasks named in UniProt numbering, structure with an offset (copying is wrong) | 7 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| The same variants on the predicted structure, without an offset (copying is right) | 7 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Helix or strand requested (a subset, reported apart) | 10 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |

This table will answer the question of the Introduction: do models map the number in a
variant name, or copy it? Four patterns are possible in its first two rows. We predict none
of them.

1. *Copying.* The target score is high where copying is right and low where it is wrong.
2. *Mapping.* The target score is high in both rows.
3. *Always converting.* The target score is low where copying is right and high where it is
   wrong. A model may have learned that file numbers usually differ from UniProt numbers and
   change the number in every case, for example by subtracting the length of a signal
   peptide. On a structure that is numbered as the request is, this turns a right number into a
   wrong one.
4. *Neither.* The target score is low in both rows. The loss then lies elsewhere, for example
   in the chain identifier or in invalid answers, and the table does not decide between
   copying and mapping.

Only pattern 2 shows that a model knows how each structure is numbered; a habit of copying or
of converting is not enough. With the grounding pack, which states the mapped residue,
patterns 1 and 3 should both turn into pattern 2. The patterns are stated on the target
score, because the task success rate also falls when an answer adds unrequested context.

The patterns describe one model, and Table 10 gives a mean over models, in which a mixture
of copying and converting models could pass for pattern 4. The question is therefore answered
model by model: SI Section S9 will give the first two rows and their difference, with its
interval, for each model. "High" and "low" have no fixed threshold. A model shows pattern 1
when the interval of its difference (copying right minus copying wrong) lies above zero, and
pattern 3 when it lies below zero. Where the interval includes zero, pattern 2 or 4 is read
from the level of the two rows, which we report and do not classify by rule.
⟦PENDING: final run — the number of models under each pattern, from the per-model rows of SI Section S9⟧

### 6.5 Follow-up turns, requests with several right answers, and planned comparisons

Table 11 divides the follow-up turns by whether a change is needed, and Table 12 holds the
planned comparisons 1 to 6 of Section 5.4.

**Table 11. Follow-up turns and requests with several right answers.** *Task success rate*:
share of answers whose drawn state is exactly right (for a request with several right answers:
the drawn state equals any one of the accepted answers), strict, mean over the models.

| Group | Scene track: tasks | Scene track: task success rate | Call-list track: tasks | Call-list track: task success rate |
|:----------|---:|---:|---:|---:|
| Follow-up turns that need a change | 48 | ⟦PENDING: final run⟧ | 36 | ⟦PENDING: final run⟧ |
| Follow-up turns that need no change | 10 | ⟦PENDING: final run⟧ | 8 | ⟦PENDING: final run⟧ |
| Requests with several right answers | 26 | ⟦PENDING: final run⟧ | 15 | ⟦PENDING: final run⟧ |

**Table 12. Planned comparisons 1 to 6 of Section 5.4.** Each row compares the task success rate (share of answers
whose drawn state is exactly right; strict, mean over the models) between two groups of tasks
or two conditions, with a 95% interval on the difference (structures resampled). *Set-aside
split*: the tasks on 15 structures that no earlier release
used; they are public too (Section 3.6). *Main*: the
main condition. *JSON mode*: the provider's option that forces syntactically valid JSON. It is
run on the models that offer it (15 of the 16
core models and each optional model that is run), with one answer per task, which is set
against the mean of the 3 main answers. *Grounding pack*: the result of an offline lookup,
including the mapped residue or the list of entries, appended to the request. *Format guide*: the text in
the system prompt that documents the answer format.

| | Comparison | Tasks | Task success rate, first group | Task success rate, second group | Difference (95% interval) |
|---:|:--------------------|---:|---:|---:|---:|
| 1 | Tasks on the other structures against the set-aside split (both tracks; all tasks) | 632 and 165 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| 2 | Full wording against terse wording (both tracks) | 30 requests (41 tasks) | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| 3 | Full wording against indirect wording (both tracks) | 30 requests (41 tasks) | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| 4 | Main against main + JSON mode (models that offer it; both tracks) | 797 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| 5 | Main against main + grounding pack (name-resolution and clinical categories, scene track) | 121 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| 6 | Main against no format guide (3 models, scene track) | 381 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |

⟦PENDING: final run — outcome counts per model (valid, unshowable by kind, schema-breaking, cut off), the repaired scores, F1 valid-only and the cost per model, as tables in SI Section S9⟧

⟦PENDING: rating study — the four results named in Section 5.5, with intervals: the share of the grader's task successes that people call the same, the share of the other answers that people call different, the same two shares for the target score, and the agreement between raters⟧

### 6.6 Preliminary evidence from the first version of the benchmark (2026)

<div class="box">

**Everything in this box is preliminary.** Findings 1 to 4 come from a pilot run of
18 October 2026: 15 models, the scene track only, 70 tasks on
14 structures, one answer per task. Finding 5 comes
from the July 2026 run of the call-list tasks of the first version, under the grader of that
time, and Finding 6 from a small trial of the rating study on the answers of the pilot run.
None of the pilot run's tasks is in the corpus of Section 3. Its answers were archived and
are graded here with the present grader (Section 4) against the references of that time, so
the scores differ somewhat from those published in October with the earlier grader. With one answer per task and
14 structures, the numbers below can show patterns; they cannot rank the
leading models.

**Finding 1: whether the answer was valid decided the ranking.** Of 1,050 answers,
784 (75%) were valid scenes. Per model the share
ranged from 9% to 99%, and strict F1
from 0.07 to 0.84 (Table 13, columns *Valid answers*
and *F1, strict*). The two are nearly proportional: the Pearson correlation between a
model's share of valid answers and its strict F1 is r = 0.99
(15 models). With the strict task success rate, by which Table 13 is
ordered, the correlation is r = 0.93. Valid-only, the models are much
closer (F1 from 0.78 to 0.95). Of the
266 invalid answers, 227 were not parseable
JSON. The text of 199 of these was archived. In
66% of the 199, the
numbers of opening and closing braces differed: a scene is a deeply nested tree, and one
brace too many or too few loses the whole answer. An offline repair of the JSON turned
183 of the 199 into scene trees (these were
not checked by the viewer). This is why the final run reports strict and valid-only scores
together and adds a JSON-mode condition.

**Table 13. Pilot run, per model (preliminary).** The run had 70 tasks and one
answer per task; the rows are ordered by the strict task success rate. Finding 1 compares the
columns *Valid answers* and *F1, strict*. *Weights*: open if the weights of the model can be downloaded,
closed if the model can be used only through a provider's service. *Valid answers*: answers
that parse and that the viewer accepts. *F1*: how much of the drawn state is right (0 to 1).
*Task success rate*: share of answers whose drawn state is exactly right. *Strict*: every answer
counts, and an unshowable answer scores 0. *Valid-only*: the mean over valid answers. The
pilot tasks stored no target, so there is no target score.

| Model | Weights | Valid answers | F1, strict | Task success rate, strict | F1, valid-only | Task success rate, valid-only |
|:--------|:---|---:|---:|---:|---:|---:|
| gemini-3.5-flash | closed | 66 of 70 | 0.84 | 71.4% | 0.89 | 75.8% |
| llama-4-maverick | open | 57 of 70 | 0.77 | 70.0% | 0.95 | 86.0% |
| deepseek-v4-flash | open | 65 of 70 | 0.80 | 68.6% | 0.86 | 73.9% |
| deepseek-v3.2 | open | 69 of 70 | 0.83 | 65.7% | 0.84 | 66.7% |
| minimax-m3 | open | 63 of 70 | 0.77 | 61.4% | 0.85 | 68.2% |
| claude-haiku-4-5 | closed | 67 of 70 | 0.80 | 60.0% | 0.84 | 62.7% |
| glm-5.2 | open | 63 of 70 | 0.76 | 58.6% | 0.85 | 65.1% |
| kimi-k2.6 | open | 51 of 70 | 0.62 | 50.0% | 0.85 | 68.6% |
| gemma-3-27b-it | open | 57 of 70 | 0.64 | 48.6% | 0.79 | 59.7% |
| qwen3-next-80b-a3b-instruct | open | 64 of 70 | 0.71 | 45.7% | 0.78 | 50.0% |
| gpt-5.4-nano | closed | 53 of 70 | 0.62 | 44.3% | 0.81 | 58.5% |
| qwen3-30b-a3b-instruct-2507 | open | 39 of 70 | 0.50 | 40.0% | 0.90 | 71.8% |
| gpt-oss-120b | open | 44 of 70 | 0.53 | 38.6% | 0.85 | 61.4% |
| gpt-oss-20b | open | 20 of 70 | 0.22 | 20.0% | 0.79 | 70.0% |
| nemotron-3-super-120b-a12b | open | 6 of 70 | 0.07 | 5.7% | 0.82 | 66.7% |

**Finding 2: clinical tasks lost their points on unrequested context, not on the residue.**
The clinical category scored lowest: strict F1 0.31, and task success
3.7%, that is 5 of
135 answers (Table 14, Figure 6). The natural reading is that finding the
residue of a variant is hard. That reading is wrong for this run. In
87 answers the requested residue was drawn exactly as in
the reference: same atoms, same representation, same colour. That is
64% of all 135 answers and
91% of the 96 valid
ones. The points were lost elsewhere. Each clinical reference of the first version also drew
a grey cartoon of the whole protein, and the requests asked only for the residue. An answer
that drew the residue alone was missing a fact; an answer that drew the cartoon differently had
a wrong one. There was a second flaw: all 9 clinical tasks
used a single structure, in which author numbers equal UniProt numbers. The residue could be
found without any mapping, so the category could not test the mapping at all. "Most answers
drew the right residue" is therefore a statement about drawing, not about mapping. Table 15
(rows 1 and 2) says what replaced both.

**Table 14. Pilot run by category, all models pooled (preliminary).** *Answers*: one per model
and task. *Valid*: answers that parse and that the viewer accepts. *F1, earlier grader*: the
score under the grader used in October, for comparison. *F1* and *task success rate*: as in
Table 13, strict, over all answers of the row. *Requested part exactly right*: this column has its
own denominator, given in each cell. Among answers to tasks whose reference marks out a
requested part against a background, it is the share that draw that part with exactly the
reference's atoms, representation and colour (an unshowable answer counts as wrong). It is the
forerunner of the target score of Section 4.2: the pilot tasks stored no target atoms, so the
requested part is taken from the reference. The first-version corpus had too few tasks in
three of its categories to show them apart, so they are pooled in one row. The last cell of
the row *All* pools the three cells above it.

| Category (first-version corpus) | Answers | Valid | F1, earlier grader | F1 | Task success rate | Requested part exactly right |
|:-----------|---:|---:|---:|---:|---:|---:|
| Translation | 615 | 491 | 0.78 | 0.77 | 69.9% | 80.0% of 105 |
| Structure-grounded, name resolution and interactions | 300 | 197 | 0.55 | 0.49 | 29.7% | 45.6% of 195 |
| Clinical variant | 135 | 96 | 0.48 | 0.31 | 3.7% | 64.4% of 135 |
| **All** | 1,050 | 784 | 0.67 | 0.63 | 49.9% | 59.8% of 435 |

![**Figure 6. Pilot run: three scores by category (preliminary).** All three are on a scale from 0 to 1 and are printed in that form (0.70 is 70% of answers; Table 14 gives the shares as percentages). *F1* (how much of the drawn state is right; a mean score) and *task success* (the share of answers whose drawn state is exactly right) are taken strictly, over all answers of all 15 models; an unshowable answer scores 0. *Requested part exactly right* has a smaller denominator in two of the three groups: it is the share, among answers to tasks whose reference marks out a requested part against a background, that draw that part exactly as the reference does, whatever the rest of the answer shows; an unshowable answer counts as wrong. The number of answers behind each bar is printed above it (n); for the third bar of a group this is the number of answers to tasks that mark a requested part. Three categories with few tasks are pooled in the middle group. In the clinical category, where every task marks a requested part, that part was usually right and the whole drawn state almost never.](generated/fig_october_regrade.svg)

**Finding 3: grounding packs did not help.** In the pilot run, unlike the final design, every
task had a grounding pack. Appending it to the request lowered task success over all
70 tasks from 49.9% to
46.3%, and the number of valid answers from 784 to
739: the longer prompt produced more invalid answers. In the clinical
category, task success was 3.7% without the pack and
3.0% with it. Finding 2 explains why the pack had little
to add: the residue was already right without it. Whether a pack helps when it holds a number
that the model cannot guess is a question for the rebuilt clinical category (Table 10).

**Finding 4: without the format guide, no answer was valid.** The condition with the
instruction and the rule for the answer only was run on 3 models, with and
without grounding packs. None of their 420 answers was a valid scene. For
these models, knowledge of the MolViewSpec format came from the prompt and not from training.

**Finding 5: the call-list track of the first version did not separate models from a keyword
script.** That track had 20 hand-written tasks and a grader that compared
call lists field by field. Under that grader the keyword script reached a mean F1 of
0.72, and the 16 models scored between
0.72 and 0.95 (run of 4 July 2026). These
numbers are the reason the track was rebuilt; they are not results of the present benchmark.

**Finding 6: the trial of the rating study was too small to validate anything.** In October,
three raters, one of them an author, gave 114 verdicts
of "same" or "different" on 109 picture comparisons of valid scenes that
the earlier grader scored below 1. Only 5 comparisons received
two verdicts, so agreement between people cannot be estimated. The trial validates neither
the image judge (Section 5.5) nor the grader, and no score in this paper uses the image
judge. SI Section S8.1 reports the trial in full, with the agreement between people and the
image judge and with its limits.

*End of the preliminary evidence.*

</div>

## 7. Errors in the first version and their corrections

The first version of MolBench (defined in Section 6) was wrong in nine ways that we know of. Table 15 lists each error, how
we found out, and what replaced it in the present version, because each error is one that
another benchmark of this kind could make.

**Table 15. Nine errors in the first version of MolBench and what replaced each in the
present version.**
*Where*: the sections that give the numbers behind the row.

| Row | What was wrong | How we found out | What replaced it | Where |
|--:|:--------|:------|:--------|:----|
| 1 | Our clinical references drew a cartoon that no request asked for, and we read the low score that followed as a difficulty of finding the residue. | A breakdown of where valid answers lost their points (Section 6.6, Finding 2). | A reference holds only what the request states. If context is wanted, the request asks for it in words. Every task stores its target where it has one, and the target score is reported beside task success in Tables 6 to 10. | Sections 3.2, 4.2; 6.6, Finding 2 |
| 2 | The clinical category could not test the mapping: all its tasks sat on one protein whose structure uses UniProt numbering. | The same analysis. | 82 tasks on 25 proteins and 31 structures; in 59 tasks the target has an offset, and results are grouped by whether copying the number in the variant name is right (it is wrong in 48). | Section 3.3.1; 6.6, Finding 2 |
| 3 | "Pathogenic" was taken from a secondary source: we first took the variants that UniProt lists as pathogenic. | A check of each candidate against the ClinVar records that UniProt cross-references. For 20% of the candidates none of these records gives the same amino-acid change a pathogenic or likely pathogenic aggregate classification, and ClinVar's aggregate classification of some variants named in tasks of the first version is "conflicting classifications of pathogenicity". | A variant is used only if ClinVar holds a record of that gene and that one change with a pathogenic or likely pathogenic classification and stated criteria (one exception, SI Section S3.2). The dates are stored. | Section 3.1; SI Section S3.2 |
| 4 | Both graders compared text: scene trees path by path, call sequences field by field. They rejected correct answers that were merely written differently, both passed some wrong ones (the scene grader 3%, the call-list grader 21%), and on the call-list track a keyword script scored close to the models. | The control set. | Both tracks are graded on drawn state, and the control set is run as a test on every change. | Section 4.5, Table 4; 6.6, Finding 5 |
| 5 | Hand-written call-list tasks had errors: label numbers where author numbers were meant, and one task that was the worked example of the prompt. | A check of those references against the structures. | Every reference is generated; a sample of references is replayed in the viewer itself; and the entry used for the worked example of both system prompts is excluded from the corpus. | Sections 3.2, 3.7 |
| 6 | Some requests had no single answer. A request to highlight "all pathogenic residues" of one protein resolved to far more residues than any user means; "show me lysozyme" was graded against one arbitrary view. | Reading the references. | Clinical requests name each variant. Requests with a countable ambiguity have their own category, with every accepted answer listed. Open-ended requests are left out. | Sections 3.3, 9.1 |
| 7 | Raters could not see what they were rating. A single highlighted residue on a whole complex was a few pixels wide, and a volunteer flagged a reference as wrong when it was only unreadable. A volunteer also found references in which two cartoons overlapped. | The trial of the rating study. | Pictures are framed on the target atoms from one shared camera. The overlapping references were corrected. The next study completes two ratings of a picture comparison before it opens new ones. | Section 5.5; 6.6, Finding 6 |
| 8 | The pilot run collected one answer per task on 14 structures, with a short limit on the length of an answer and no record of how often an answer was cut off. | Planning the final run. | 3 answers per task, 78 structures, a limit of 8,000 tokens, and the provider's reason for the end of each answer archived. | Sections 5.3, 5.4 |
| 9 | The prompts taught answers that the graders marked wrong, and other faults of the same kind (below). | Four reviews of the benchmark by language models before the final run. | Each finding was fixed in the generator or the grader and is now covered by an automated test and by a new kind of control. Both prompt examples are graded by the benchmark's own grader as a test. | Sections 3.1, 4.5; SI Section S5 |

Row 9 needs more words than a table cell holds. Before the final run, the benchmark was
reviewed four times by language-model reviewers, each given one role (structural biologist,
clinical geneticist, benchmark methodologist, tester of the grader). The reviewers wrote
natural answers by hand and graded them, and we reproduced each finding before acting on it.
Four examples: the worked example of each prompt was written in a way that the references,
or many generated tasks, did not accept; a residue named by UniProt number on a predicted
structure was scored as selecting nothing; and a scene that named a file which the viewer
cannot load was graded as a success. The same reviews found clinical requests whose
"pathogenic" record belonged to another gene or to two variants taken together (SI Section
S3.2).

## 8. Discussion

⟦PENDING: final run — discussion of the results: which categories separate models, what the paired comparison shows, whether the set-aside split differs from the other tasks, and what Table 10 says about mapping against copying⟧

Two points can be made before the final run, because they concern the instrument and not the
models.

**One score is not enough.** The pilot run gave three different pictures of the same answers
(Section 6.6). Strict scores mostly measured whether a model returned a scene that the viewer could load. F1 in the
clinical category mostly measured whether a model reproduced a background. Only a score
restricted to the requested atoms showed that the residue was usually drawn right, and this
in a pilot category that needed no mapping (Section 6.6, Finding 2). We therefore
report the task success rate and the target score together, both strict and valid-only, and
F1 for partial credit; Box 2 says which of the two is primary in which table.

**A benchmark's references need the same scrutiny as the models.** The most important finding
so far concerns our own references (Table 15, row 1). It was found by asking where valid
answers lost their points, and not by looking at totals. We recommend that analysis to anyone
who builds a benchmark with partial credit.

## 9. Limitations

Four limits bound the claims of this paper more than the others: each track is graded by the
rules of one viewer; the requests come from templates; the tasks are public; and the grader
has been tested only against cases that we foresaw. The full list follows in four groups.

### 9.1 Scope

- **One viewer per track.** The scene track is graded by the rules of Mol\* 5.9.0, and the
  call-list track by those of PDBe Mol\* 3.3.2. MolViewSpec is designed to be independent of the
  viewer, but Mol\* is its implementation in practice. We make no claim about PyMOL, ChimeraX
  or VMD.
- **No lookup, one answer.** A model cannot look anything up, ask a clarifying question, or see the picture.
  A product that wraps a model in tools, validation and retries may do better. We measure the
  model, not such a product.
- **No open-ended tasks.** Requests such as "show the active site clearly" have no single
  right drawn state and are not in the corpus. Requests with a countable ambiguity are, in a
  small category.

### 9.2 Corpus

- **Generated requests.** Requests come from templates. They are cleaner than what people
  type. They have been read for naturalness by the authors and by the language-model reviewers
  of Section 7, not yet by an independent structural biologist. The terse and indirect
  phrasings were written out one by one by the language-model coding assistant used in this
  work, and checked by rule for dropped values; no person has read them all.
- **Public tasks and contamination.** Earlier MolBench tasks have been public since May 2026,
  and the whole corpus, set-aside split included, was in a public repository before the run. A
  model trained later may have seen any of it. The set-aside split does not solve this: it
  compares two sets of structures, not seen tasks with unseen tasks (Section 3.6). It cannot
  show that a model has, or has not, memorised tasks, and it cannot protect future runs. The
  generators are seeded, so a fresh split on new structures can be generated.
- **A panel of 79 structures.** The structures were chosen by hand for coverage and
  are mostly well known: the median year of deposition is 1999, and only
  10 entries date from 2020 or later. Scores on them may be higher
  than on a recent entry that a model has never read about. All but
  2 entries have at most 15,000 atoms, so large
  assemblies are not tested.
- **Classifications change, and sources differ.** ClinVar classifications change as evidence
  is submitted. Ours are a snapshot of 12 November 2026 to
  16 November 2026. Sources also differ on one day: for
  20% of the candidates that UniProt lists as pathogenic or likely
  pathogenic, none of the ClinVar records that UniProt cross-references gives the same
  amino-acid change such an aggregate classification (Section 3.1). The residue that a name
  points to does not depend on the classification, and no task asks for a judgement about
  disease.
- **Records with little review.** The clinical requests name 87 distinct
  variants (a variant that is asked about on two structures is counted once). For
  each variant we take its *best-reviewed record*: of its qualifying records (Section 3.1),
  the one with the highest review status. For
  15 variants, the running example among them, this record has the review
  status "criteria provided, single submitter": one submitter, with stated
  criteria, and no confirmation by a second submitter or an expert panel. For
  52 it has several submitters and no conflicts, and for
  19 it was reviewed by an expert panel or comes from a
  practice guideline. One variant, lysozyme p.Ile74Thr, is used although its record states
  no criteria (Section 3.1).
- **What we did not check in ClinVar.** We looked only at the ClinVar records that UniProt
  cross-references. A record lists the protein change once for each transcript of the gene;
  we accept it if any one of these names equals our amino-acid change and position, and we
  did not check which transcript that name is counted on. If it numbers the protein
  otherwise than the UniProt canonical sequence does, the record is about another residue
  than the one we ask for; the reference atoms would still be those of the UniProt position
  in the request. A request that states no accession rests on the same assumption for the
  protein of the gene's MANE Select transcript (Section 3.3.1). A request also attaches
  ClinVar's classification to a protein-level name and names no condition, which ClinVar
  itself does not do (Section 3.1). And one qualifying record is enough: we did not look for
  further records of the same amino-acid change that are classified differently.

### 9.3 Grader

- **Tested only against cases we foresaw.** The grader makes no error on the control set
  because it was corrected until it made none (Section 4.5). How often it misjudges a way of
  writing an answer that the control set lacks is not known. The human check of the grader has
  so far been run only as a trial with three raters (Section 6.6). Until the
  planned study is done, the evidence that task success matches what people see is the control
  set and the read-back from the viewers.
- **UniProt selections were not replayed in the viewer.** The call-list references of the
  clinical category select by UniProt accession and position. The grader resolves these
  through the frozen SIFTS table; for PDB entries this path was not compared with the running
  viewer (Sections 3.4 and 3.7).
- **Name resolution: text comparison outside the panel.** Of the
  5,778 entries that the name-resolution tasks accept,
  5,736 are outside the panel, and an answer on one of them
  is compared with the reference as text, so a correct answer that is spelled differently
  fails (the weaker rule of Section 4.1). Table 8 reports such answers in a row of their
  own.
- **The file behind the call-list viewer.** The atom tables are built from the archive file of
  each entry, and the read-back loaded that file into both viewers. Left to itself, PDBe Mol\*
  fetches PDBe's own copy of the entry, which carries the SIFTS mapping. We did not compare
  the two copies atom record by atom record.
- **Partial credit is a choice.** Facts have equal weight, and a wrong colour or opacity
  counts half. On
  the call-list track any other change to the right atoms counts half as well, so F1 is not
  the same measure on the two tracks (Section 4.2). Other choices would give other F1 values.
  Task success does not depend on them.
- **What the grader does not model.** Atoms are compared on the coordinates as deposited;
  selections of single symmetry copies of a biological assembly are not modelled. The
  appearance of labels, sizes and camera coordinates are not graded. Four features of the
  call-list viewer that fetch data from live services are graded only as settings that the
  answer switched on. SI Section S4.8 gives the full list.

### 9.4 Run

- **What the run can and cannot detect.** Means per category and track rest on
  15 to 178 tasks (Table 8); the smallest
  categories are estimated loosely. Several planned
  contrasts are descriptive only: the set-aside split against the other tasks within one
  category (the set-aside tasks sit on 15 structures); the
  10 helix and strand tasks; the terse and indirect phrasings within one category
  (30 requests in all); and the matched clinical tasks. Table
  10 reports 7 sets of matched tasks, on
  4 proteins. (8 sets ask
  about the same variant on a structure with an offset and on one without; one of them uses
  a traditional name and is left out, Section 3.3.1.) In every set the structure without an
  offset is a predicted structure, so "no offset" and "predicted structure" cannot be told
  apart. We report these contrasts with intervals and do not test them.
- **The viewer can do the mapping on one track only.** On the call-list track the viewer can
  map a UniProt position itself; on the scene track the model must. The paired comparison is
  therefore reported with and without the clinical pairs (Sections 3.4 and 6.3).
- **The two system prompts differ in length.** The system prompt has 1,328
  words on the scene track and 1,556 on the call-list track (Section 5.2),
  and in the pilot run a longer prompt lowered the share of valid answers. A difference
  between the tracks can therefore come from the prompt as well as from the format.
- **Structures of one protein are resampled separately.** Intervals resample structures. In
  the clinical category, 6 proteins have tasks on more
  than one structure, and matched tasks ask about the same variant on two structures. Such
  structures are not independent, so intervals in this category are somewhat too narrow.
- **The floor.** The keyword script is a weak floor. The literal script is a stronger one:
  with no knowledge of any structure it solves a share of the
  translation category, and in the clinical category copying the number in the variant name
  is right in 34 of the 82 tasks (Section 3.3.1). Clinical
  results are therefore grouped by that property, and follow-up results by whether the right
  answer is to change nothing.
- **Prices and hosted models change.** Costs are list prices on the day of the run. Hosted
  models are updated and withdrawn; the archived answers are the lasting record.

## 10. Conclusion

MolBench grades how a language model drives a molecular viewer on the atoms, representations
and colours that the viewer would draw, without a judge model. References are computed by
script from the structure and, for clinical variants, from the SIFTS mapping and ClinVar.
The corpus has 797 tasks on 78 structures;
258 requests are posed both as a MolViewSpec scene and as a list of
viewer calls, so that an error of content can be told apart from an error of format.
Three things hold before any final result. On a control set of 2,175 answers the
grader agrees with every known verdict, where our earlier graders, which compared text, rejected
44% and 55% of the
correct answers; the control set is the one against which the grader was developed, and a
check by people is planned. One score is not enough: we report the task success rate, the
target score and F1. And the pilot run taught two things. Over all tasks, most points were
lost to answers that the viewer could not show at all. In the clinical category, most were
lost to our own references, which drew a cartoon that the requests did not ask for. That
category did not yet test the mapping of residue numbers. In the rebuilt category, copying
the number from the variant name gives the wrong residue in 48 of
82 tasks, and the final run will show whether models copy it.
⟦PENDING: final run — two sentences on the results: how well the models drive the viewer on each track, and what the paired comparison shows⟧

## 11. Ethics, human participants and licences

**No patient data.** The benchmark contains no data about individuals. Clinical variants come
from UniProt's variant annotation and are confirmed in ClinVar's public variant-level
records; no individual-level data are used. A variant
serves only as a residue position with a classification label.

**Not for clinical use.** A high score does not make a model fit to interpret variants. The
clinical category measures whether a model can locate a residue in a structure. The data providers
say the same of their data: UniProt and the AlphaFold Protein Structure Database state that
their content is not a substitute for professional medical advice. ⟦PENDING: Dan — ClinVar's own statement on clinical use, to be read at the source by hand and added to this sentence; the page refuses automated reading⟧

**Volunteer raters.** The rating study asks volunteers to compare pictures of a molecule,
a reference and a model answer at a time. It collects their answers, optional free-text notes
and the time taken per item. Raters are identified in the analysis by pseudonyms; no names,
contact details or rater identifiers are published. ⟦PENDING: Dan — confirm the consent wording shown to raters, and whether the target journal or the author's institution requires an ethics statement or a waiver for this study⟧

**Use of language models in this work.** Language models are the subject of the study. They
were also used as coding and drafting assistants in building the benchmark and in writing
this manuscript. The authors checked all content and are responsible for it.
⟦PENDING: Dan — final wording of this disclosure, which the journal asks for in the Acknowledgements⟧

**Licences of data and software.** We read each licence at its source on 16 November 2026 (Table
16). Frozen copies of third-party data in the repository keep their original terms and are
attributed in the repository.

**Table 16. Data and software used, with licence or terms as stated at the source.**

| Resource | Used for | Licence or terms | Read at |
|:---|:---|:---|:---|
| Protein Data Bank archive and RCSB PDB web services [24] | structure files, atom tables, entry annotations | CC0 1.0 public-domain dedication | rcsb.org/pages/usage-policy |
| PDBe: SIFTS mapping, updated structure files, search of entries per protein [8, 28] | residue mapping, choice of structures | EMBL-EBI terms of use: no additional restrictions on use or redistribution; attribution expected | ebi.ac.uk/about/terms-of-use |
| UniProt [7] | sequences, candidate variants | CC BY 4.0 | uniprot.org/help/license |
| ClinVar [6] | classification of variants | NCBI molecular data policy: NCBI places no restrictions on use or distribution; submitters may hold rights | ncbi.nlm.nih.gov/home/about/policies |
| AlphaFold Protein Structure Database [25, 26] | 5 predicted structures | CC BY 4.0 | alphafold.ebi.ac.uk (licence and disclaimer) |
| Mol\* [16] and MolViewSpec [20] | scene format, validation, read-back, pictures | MIT | github.com/molstar |
| PDBe Mol\* [22] | viewer of the call-list track | Apache-2.0 | github.com/molstar/pdbe-molstar |
| ipymolstar [23] | Python host of that viewer | MIT | pypi.org/project/ipymolstar |
| GEMMI [29] | reading structure files | MPL-2.0 | github.com/project-gemmi/gemmi |
| json-repair [35] | repair counterfactual | MIT | github.com/mangiucugna/json_repair |

MolBench's own code, tasks and references are released under the MIT licence.

## 12. Data and Software Availability

- **Code, tasks, references, graders, control set:** <https://github.com/dbolser/MolBench>
  (MIT licence). ⟦PENDING: corpus freeze — version tag and hash of the frozen corpus⟧
- **Archive:** ⟦PENDING: deposit — DOI of the frozen corpus, including the set-aside split, and of the raw model answers and score files of the final run⟧
- **Rating data:** ⟦PENDING: deposit — anonymised ratings of both rating studies, with the analysis scripts⟧
- **Results browser:** <https://dbolser.github.io/MolBench/>.
- **This paper:** every table, figure and number in this paper is regenerated by scripts in
  the repository from the task files, the frozen data and the archived answers; the
  repository's notes on the paper say how.

Grading needs no network access and no paid service. Validation by the viewer and the pictures
for the rating study need a browser without a display and the Mol\* bundle, both free.

## Supporting Information

The Supporting Information (one PDF file) contains: background terms of structural biology and of the corpus
(Section S0, with the names that the repository uses); the running example in full (S1); all task templates with an example request
each (S2); the structure panel, how it was chosen, and the list of variants (S3); the full
grading rules and the known limits of the grader (S4); the control set by kind (S5); the run
manifest, the models and their prices (S6); the system prompts (S7); further tables of the
pilot run and the trial of the rating study (S8); and further tables of the final run (S9,
pending).

## Author information

⟦PENDING: Dan — corresponding author, author contributions, and the notes the journal asks for (competing interests)⟧

## Acknowledgements

⟦PENDING: Dan — acknowledgements, funding, and the disclosure of language-model use⟧

## References

1. Goddard T. Claude Chat to operate ChimeraX. *UCSF RBVI web page, 4 December 2025*. <https://www.rbvi.ucsf.edu/chimerax/data/claude-dec2025/claude_mcp.html>
2. Mol* developers. Prism viewer (pull request 1978) and v6: PyMOL and VMD commands (pull request 2052), molstar/molstar. *Source-code pull requests, merged 2026-10-16 and 2026-10-25*. <https://github.com/molstar/molstar/pull/1978>
3. Navarro C, Torrens-Fontanals M, Thölke P, Doerr S, De Fabritiis G. Speak to a Protein: An Interactive Multimodal Co-Scientist for Protein Analysis. *Journal of Chemical Information and Modeling* 2026;66(19):12391–12401. Preprint: arXiv:2510.17826. doi:[10.1021/acs.jcim.6c01738](https://doi.org/10.1021/acs.jcim.6c01738)
4. Sun J, Li A, Deng Y, Li J. ChatMol Copilot: An Agent for Molecular Modeling and Computation Powered by LLMs. *Proceedings of the 1st Workshop on Language + Molecules (L+M 2024)*:55–65. doi:[10.18653/v1/2024.langmol-1.7](https://doi.org/10.18653/v1/2024.langmol-1.7)
5. Faezov B, Dunbrack RL. PDBrenum: A webserver and program providing Protein Data Bank files renumbered according to their UniProt sequences. *PLOS ONE* 2021;16(7):e0253411. doi:[10.1371/journal.pone.0253411](https://doi.org/10.1371/journal.pone.0253411)
6. Landrum MJ, Lee JM, Benson M, Brown GR, Chao C, Chitipiralla S, Gu B, Hart J et al. ClinVar: improving access to variant interpretations and supporting evidence. *Nucleic Acids Research* 2018;46(D1):D1062–D1067. doi:[10.1093/nar/gkx1153](https://doi.org/10.1093/nar/gkx1153)
7. The UniProt Consortium. UniProt: the Universal Protein Knowledgebase in 2025. *Nucleic Acids Research* 2025;53(D1):D609–D617. doi:[10.1093/nar/gkae1010](https://doi.org/10.1093/nar/gkae1010)
8. Dana JM, Gutmanas A, Tyagi N, Qi G, O'Donovan C, Martin M, Velankar S. SIFTS: updated Structure Integration with Function, Taxonomy and Sequences resource allows 40-fold increase in coverage of structure-based annotations for proteins. *Nucleic Acids Research* 2019;47(D1):D482–D489. doi:[10.1093/nar/gky1114](https://doi.org/10.1093/nar/gky1114)
9. Sun Q, Liu Z, Ma C, Ding Z, Xu F, Yin Z, Zhao H, Wu Z et al. ScienceBoard: Evaluating Multimodal Autonomous Agents in Realistic Scientific Workflows. *arXiv preprint* 2025. v3 is marked “ICLR 2026 Camera Ready Version”. arXiv:[2505.19897](https://arxiv.org/abs/2505.19897)
10. Dai D, Qi H, Liu L, Li Y, Chen B, Dou Z, Zeng Q, Kang Q et al. OSWorld-Science: A Benchmark of Computer Use Agents for Learning and Using Scientific Software. *arXiv preprint* 2026. arXiv:[2609.39903](https://arxiv.org/abs/2609.39903)
11. Ai K, Miao H, Tang K, Gorski N, Sun J, Liu G, Ingolfsson HI, Lenz D et al. SciVisAgentBench: A Benchmark for Evaluating Scientific Data Analysis and Visualization Agents. *arXiv preprint* 2026. arXiv comment: IEEE Transactions on Visualization and Computer Graphics (IEEE VIS '26). arXiv:[2603.29139](https://arxiv.org/abs/2603.29139)
12. Goddard TD, Huang CC, Meng EC, Pettersen EF, Couch GS, Morris JH, Ferrin TE. UCSF ChimeraX: Meeting modern challenges in visualization and analysis. *Protein Science* 2018;27(1):14–25. doi:[10.1002/pro.3235](https://doi.org/10.1002/pro.3235)
13. Xie T, Zhang D, Chen J, Li X, Zhao S, Cao R, Toh JH, Cheng Z et al. OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments. *arXiv preprint* 2024. arXiv:[2404.07972](https://arxiv.org/abs/2404.07972)
14. Qin Y, Liang S, Ye Y, Zhu K, Yan L, Lu Y, Lin Y, Cong X et al. ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs. *arXiv preprint* 2023. arXiv:[2307.16789](https://arxiv.org/abs/2307.16789)
15. Yao S, Shinn N, Razavi P, Narasimhan K. tau-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains. *arXiv preprint* 2024. arXiv:[2406.12045](https://arxiv.org/abs/2406.12045)
16. Sehnal D, Bittrich S, Deshpande M, Svobodová R, Berka K, Bazgier V, Velankar S, Burley SK et al. Mol* Viewer: modern web app for 3D visualization and analysis of large biomolecular structures. *Nucleic Acids Research* 2021;49(W1):W431–W437. doi:[10.1093/nar/gkab314](https://doi.org/10.1093/nar/gkab314)
17. Jia D, Irger A, Besançon L, Strnad O, Luo D, Björklund J, Kouyoumdjian A, Ynnerman A et al. VOICE: Visual Oracle for Interaction, Conversation, and Explanation. *IEEE Transactions on Visualization and Computer Graphics* 2025;31(10):8828–8845. Preprint: arXiv:2304.04083. doi:[10.1109/TVCG.2025.3579956](https://doi.org/10.1109/TVCG.2025.3579956)
18. Cortes Rodriguez F, Abriata L. Speech recognition assisted by large language models to command software orally -- Application to an augmented and virtual reality web app for immersive molecular graphics. *arXiv preprint* 2026. arXiv:[2603.02901](https://arxiv.org/abs/2603.02901)
19. RenhaoL. molstar-mcp: a Model Context Protocol server that builds MolViewSpec scenes for Mol*. *Software, MIT; repository created 2026-05-31*. <https://github.com/RenhaoL/molstar-mcp>
20. Midlik A, Bittrich S, Fleming JR, Nair S, Velankar S, Burley SK, Young JY, Vallat B et al. MolViewSpec: a Mol* extension for describing and sharing molecular visualizations. *Nucleic Acids Research* 2025;53(W1):W408–W414. doi:[10.1093/nar/gkaf370](https://doi.org/10.1093/nar/gkaf370)
21. Bittrich S, Midlik A, Varadi M, Velankar S, Burley SK, Young JY, Sehnal D, Vallat B. Describing and Sharing Molecular Visualizations Using the MolViewSpec Toolkit. *Current Protocols* 2024;4(7):e1099. doi:[10.1002/cpz1.1099](https://doi.org/10.1002/cpz1.1099)
22. PDBe. PDBe Molstar (pdbe-molstar): the PDBe implementation of Mol*, version 3.3.2. *Software, Apache-2.0; version 3.3.2 published on npm 2024-11-25*. <https://github.com/molstar/pdbe-molstar>
23. Smit J, ipymolstar contributors. ipymolstar: Mol* as an anywidget, version 0.1.0. *Software, MIT; version 0.1.0 released on PyPI 2025-04-10*. <https://github.com/molstar/ipymolstar>
24. wwPDB consortium. Protein Data Bank: the single global archive for 3D macromolecular structure data. *Nucleic Acids Research* 2019;47(D1):D520–D528. doi:[10.1093/nar/gky949](https://doi.org/10.1093/nar/gky949)
25. Varadi M, Bertoni D, Magana P, Paramval U, Pidruchna I, Radhakrishnan M, Tsenkov M, Nair S et al. AlphaFold Protein Structure Database in 2024: providing structure coverage for over 214 million protein sequences. *Nucleic Acids Research* 2024;52(D1):D368–D375. doi:[10.1093/nar/gkad1011](https://doi.org/10.1093/nar/gkad1011)
26. Jumper J, Evans R, Pritzel A, Green T, Figurnov M, Ronneberger O, Tunyasuvunakool K, Bates R et al. Highly accurate protein structure prediction with AlphaFold. *Nature* 2021;596(7873):583–589. doi:[10.1038/s41586-021-03819-2](https://doi.org/10.1038/s41586-021-03819-2)
27. PDBe-KB consortium. PDBe-KB: a community-driven resource for structural and functional annotations. *Nucleic Acids Research* 2020;48(D1):D344–D353. doi:[10.1093/nar/gkz853](https://doi.org/10.1093/nar/gkz853)
28. PDBe-KB consortium. PDBe-KB: collaboratively defining the biological context of structural data. *Nucleic Acids Research* 2022;50(D1):D534–D542. doi:[10.1093/nar/gkab988](https://doi.org/10.1093/nar/gkab988)
29. Wojdyr M. GEMMI: A library for structural biology. *Journal of Open Source Software* 2022;7(73):4200. doi:[10.21105/joss.04200](https://doi.org/10.21105/joss.04200)
30. Vollmar M, Westrip S, Nair S, Balasubramaniyan B, Velankar S, Jones L, Strickland P. Associating protein residues in the literature with structural data. *Acta Crystallographica Section D Structural Biology* 2026;82(2):113–125. doi:[10.1107/S2059798326000021](https://doi.org/10.1107/S2059798326000021)
31. Li Z, Kong X, Su J, Ma Z, Li M, Li S, Zhang Y, Rong Y et al. From Macro to Micro: Benchmarking Microscopic Spatial Intelligence on Molecules via Vision-Language Models. *arXiv preprint* 2025. arXiv:[2512.10867](https://arxiv.org/abs/2512.10867)
32. den Dunnen JT, Dalgleish R, Maglott DR, Hart RK, Greenblatt MS, McGowan-Jordan J, Roux AF, Smith T et al. HGVS Recommendations for the Description of Sequence Variants: 2016 Update. *Human Mutation* 2016;37(6):564–569. doi:[10.1002/humu.22981](https://doi.org/10.1002/humu.22981)
33. Hart RK, Fokkema IFAC, DiStefano M, Hastings R, Laros JFJ, Taylor R, Wagner AH, den Dunnen JT. HGVS Nomenclature 2024: improvements to community engagement, usability, and computability. *Genome Medicine* 2024;16(1):149. doi:[10.1186/s13073-024-01421-5](https://doi.org/10.1186/s13073-024-01421-5)
34. Morales J, Pujar S, Loveland JE et al. A joint NCBI and EMBL-EBI transcript set for clinical genomics and research. *Nature* 2022;604(7905):310–315. doi:[10.1038/s41586-022-04558-8](https://doi.org/10.1038/s41586-022-04558-8)
35. Baccianella S. json_repair: repair malformed JSON from LLMs, APIs, logs, and user input in Python. *Software, MIT* 2026. <https://github.com/mangiucugna/json_repair>
36. Efron B. Bootstrap Methods: Another Look at the Jackknife. *The Annals of Statistics* 1979;7(1):1–26. doi:[10.1214/aos/1176344552](https://doi.org/10.1214/aos/1176344552)
37. McNemar Q. Note on the Sampling Error of the Difference Between Correlated Proportions or Percentages. *Psychometrika* 1947;12(2):153–157. doi:[10.1007/BF02295996](https://doi.org/10.1007/BF02295996)
