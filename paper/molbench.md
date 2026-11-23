<!-- Built by paper/build.py from paper/sections/ and paper/generated/*.json (run numbers: October 2026 panel, PRELIMINARY). Do not edit: edit the sources. -->

# MolBench: Grading Language Models on What a Molecular Viewer Would Show

⟦PENDING: Dan — author list, affiliations, corresponding author⟧

*Draft for review. Every number is written by a script. A cell or sentence marked PENDING in
double brackets waits for the final run or for an author decision. The only results that
exist today come from a first version of the benchmark and are boxed in Section 6.6.*

⟦PENDING: Dan — graphic for the table of contents, which the journal asks for⟧

## Abstract

Language models now drive molecular viewers, and a wrong picture looks as polished as a
right one. MolBench grades by rule, without a judge model, what the Mol\* viewer would draw:
which atoms, in which representation (spheres, sticks or cartoon ribbon) and colour. The model sees only the
request and a format guide: no structure file, no lookup. Scripts compute references
from structure files, a residue-numbering table (SIFTS) and a variant archive (ClinVar). Of eight task categories
(797 tasks, 78 structures), one asks for the residue
(amino acid) replaced by a variant that ClinVar classifies as pathogenic or likely
pathogenic. The variant's name usually gives a position in the protein's reference sequence
(UniProt); the structure often numbers that residue differently. Do models convert the
number, or copy it? To separate content from format errors,
258 requests are answered in two formats: a scene description
(MolViewSpec) and a list of viewer calls (PDBe Mol\*). The three scores are task success
(drawing exactly right), a target score (requested atoms marked exactly; background
ignored) and F1 (partial credit). The grader agrees with all 2,175 control answers
used to develop it. A pilot run exposed two errors in our own references, now corrected.
⟦PENDING: final run — main results on both tracks and the paired comparison, with the number of models, in two sentences, which replace the sentence on the pilot run so that the abstract stays within its limit⟧

## 1. Introduction

Molecular viewers are how structural biologists look at their data, and they are hard to
drive. The data are *structures*: the three-dimensional atom coordinates of molecules. To
show one residue (one amino acid) of one protein chain, a user must know how the viewer
writes a selection, how the chain is named, and which of several residue numberings
applies. Language models promise to remove that barrier: the user says what they want, and
the model writes the commands. Several viewers now ship such assistants or can be operated
by one [1–4].

Whether these assistants are right is rarely measured, and a wrong answer is hard to see.
One request, which we follow through this paper, shows why:

> *"PDB entry 2NWD: the LYZ (Lysozyme C, UniProt P61626) variant p.W82R is classified as pathogenic in ClinVar. Show the residue it replaces as yellow spacefill spheres."*

Here 2NWD is an *entry* of the Protein Data Bank (PDB), one deposited structure, and
p.W82R is a variant that turns a tryptophan (W) into an arginine (R). The
request asks for that tryptophan. A model that takes the 82 of the name
as the residue number selects residue 82 of the file, which is a serine.
It returns a clean picture of the wrong amino acid, and nothing in the picture says so. The
tryptophan is residue 64 of this file.

The two numbers come from two ways of counting. Position 82 is counted
along the sequence of human lysozyme in UniProt, the reference database of protein
sequences. That sequence begins with the 18-residue signal peptide, which the cell cuts off; the file
numbers the chain from the first residue of the protein that is left. The case is not
unusual: in a survey of the PDB, 38.6% of 176,507 entries contained proteins that are not
numbered as their UniProt sequences are [5].

**What the model is given.** In MolBench the model receives only the request and a guide to
the answer format. It does not see the structure file, it cannot look anything up, and it
does not see the picture that its answer produces. To answer the request above it must know
from its training how entry 2NWD is numbered, as a model that is used without tools must. The classification in the request
comes from ClinVar, a public archive of human genetic variants; the benchmark uses a variant
only as an address for a residue and never asks whether it causes disease.

**Thesis.** Whether a language model has driven a molecular viewer correctly can be decided
by rule, without a second model as judge, if two conditions hold: each reference answer is
computed from the structure itself, and each answer is graded on what the viewer would draw,
not on how the answer is written.

MolBench is built on this thesis (Figure 1). The reference for the request above is not
written by a person. A script reads the variant from ClinVar [6], maps its
UniProt position [7] to the residue of the entry with SIFTS [8], a
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

![**Figure 1. From public data to a score.** Frozen public data are turned into tasks by generator scripts; each model is given the format guide and the request, and answers each task three times; the grader resolves the reference and the answer to their drawn state and compares them. Below the steps: the four checks that involve no model (Section 3.7). A *pair* is one request posed on both tracks. *Set-aside structures*: 15 structures that the first version of the benchmark (public from May 2026) never used; their tasks are public too. *Task success*: the drawn state is exactly right. *Target score* (0 to 1): how exactly the answer marks out the requested atoms; any other drawing, such as a cartoon of the protein (a ribbon that traces the chain), is ignored. *F1*: how much of the drawn state is right, with partial credit. *Strict* and *valid-only* are the two main ways to average a score (Section 4.4).](generated/fig_pipeline.svg)

This paper makes four contributions.

1. **A corpus built by script** (Section 3): 797 tasks on
   78 structures in eight categories. In 48 of
   its 82 clinical requests, a model that copies the number from the variant name
   selects the wrong residue.
2. **A grader on drawn state** (Section 4), with three scores, tested on 2,175
   control answers whose verdict is known from how they were made.
3. **A paired design** (Sections 3.4 and 5.4). An answer is a MolViewSpec scene, which
   describes what the Mol\* viewer should load and draw (the *scene track*), or an ordered
   list of calls to the PDBe Mol\* viewer (the *call-list track*).
   258 requests are posed on both tracks, with the same target atoms, so
   that an error of content can be told apart from an error of format.
4. **A pilot that corrected the benchmark, and a fixed plan for the final run** (Sections 5 to 7). A pilot run exposed errors in our own references (Table 13, rows 1 and 2), and the analysis of the final
   run (tables, comparisons and primary scores) was fixed before any model was called.
   ⟦PENDING: final run — one sentence stating the main result⟧

## 2. Related work

**Benchmarks.** The closest published benchmarks test agents that operate scientific
software on a desktop through screenshots and clicks. ScienceBoard [9]
includes tasks in UCSF ChimeraX [10] and checks the state of the
application afterwards; OSWorld-Science [11, 12] includes
PyMOL in one of its software configurations. SciVisAgentBench [13] scores
scientific visualizations, some of them molecular, with a language-model judge. General
benchmarks of tool use [14, 15] check that the right function is
called with the right arguments. We found no benchmark that grades the atoms a viewer would
draw against references computed from the structure, and none that tests the mapping of
residue numbers.

**Assistants.** Assistants that drive a molecular viewer exist for Mol\*
[2, 3, 16], PyMOL [4], ChimeraX
[1] and for speech interfaces [17, 18]. In their papers
and documentation we found no measurement of how accurately they drive the viewer. One community tool states that
the residue numbers which researchers take from ClinVar and the literature "are always
author numbers" [16]; that fails for many entries [5], and it is
the error our clinical category is built to detect.

**Data and software.** MolViewSpec describes a molecular scene as a tree of typed nodes and
is implemented in Mol\* [19–21]; the call-list
track targets the PDBe build of Mol\* [22, 23]. Residue mentions in the
literature have been mapped to structures through SIFTS before [24], and
vision-language models read rendered molecules well below human level [25],
which is one reason our scores do not rest on a model that looks at pictures. SI Section S15
describes each of these works; where we say that a work lacks something, we mean that we did
not find it in the cited source.

## 3. Building the benchmark

A task is a request on one track, a reference answer, a record of how the reference was
made and, for most tasks, the atoms that the request is about (the *target*). No reference
is written by hand. Box 1 defines the main terms; SI Section S0 is the full glossary.

<div class="box">

**Box 1. Terms.** *Model* always means a language model.

| Term | Meaning in this paper |
|:---------|:------------------------------|
| Author numbering | The chain names and residue numbers chosen by the depositors of a structure. Papers and most viewers show these. |
| Label numbering | The chain names and residue numbers assigned by the archive: 1, 2, 3 … along the full sequence of the molecule in the sample, including residues that have no coordinates. |
| UniProt numbering | The position of a residue in UniProt's canonical sequence of the protein, counted from its first residue (the initiator methionine included). A variant name with the prefix "p." (p.W82R, or p.Trp82Arg) is in this numbering here. |
| Traditional name | A variant name from older literature, without "p.", numbered from the first residue of the *mature protein* (W64R for p.W82R). The mature protein is what remains after the cell has cut off the leading segment: a signal peptide, sometimes with a propeptide, or the initiator methionine alone. |
| Offset | For one residue, its UniProt number minus its author number (82 − 64 = 18 in the running example). A residue *has an offset* when the two differ. |
| Copying the number | Using the number printed in a variant name as the author residue number. Copying is *right* in a task if the answer written in this way is exactly right, and *wrong* otherwise. |
| Scene, call list | The two answer formats. A *scene* (MolViewSpec) states what to load and draw; nothing is on screen unless the scene says so. A *call list* is an ordered list of calls to the PDBe Mol\* viewer, which starts from a *default view*: the whole structure, with the polymer chains as a cartoon (a ribbon that traces each chain). |
| Track | One of the two halves of the benchmark: *scene track* and *call-list track*, named after the answer format. |
| Pair, side | A *pair* is one request posed on both tracks, with the same target atoms. A *side* is one of its two tasks. |
| Target | The atoms that the request is about (Section 4.2). |

</div>

### 3.1 Frozen public data

**Structures.** All tasks use a fixed *structure panel* of 79 structures:
74 PDB entries [26] and 5 predicted structures from
the AlphaFold Protein Structure Database [27, 28], which use
UniProt numbering. One
entry is reserved for the worked example of the system prompts, so tasks use
78. The panel was chosen by hand for coverage, not at random. In 46 of the 79 structures at least one residue
has an offset. Every feature that we claim for a structure is verified in its file by the
build script (SI Section S3.1).

**Variants.** The panel includes structures of 27 human proteins in which germline missense variants cause single-gene
disease. A *missense* variant replaces one amino acid by another; *germline* means present
in every cell of a person, inherited or newly arisen, not acquired in a tumour. A variant
here is one amino-acid change, of which ClinVar may hold several
DNA-level records. UniProt lists 3,352 such variants of these proteins as pathogenic or
likely pathogenic. We keep a variant only if it has a *qualifying record*: a ClinVar
variation record, cross-referenced by UniProt, that meets four conditions. It lists the same
amino-acid change at the same position; its aggregate germline classification (ClinVar's
summary over all submitters) is pathogenic, likely pathogenic or pathogenic/likely
pathogenic; it is a record of the gene named in the request and of that change alone, not
of a haplotype (several changes inherited together); and its review status is not "no
assertion criteria provided", which means that no submitter said by which criteria the
variant was classified. This leaves a pool of 2,400 variants, from which
the generator draws. The clinical tasks name 87 variants (a few tasks name
several) on 25 of the 27 proteins:
86 from the pool and one exception made by hand from outside it,
lysozyme p.Ile74Thr, among the first variants reported to cause lysozyme amyloidosis, whose record
states no assertion criteria (one task per track). SI Section
S3.2 gives the filter step by step and what a request says about the classification.

**Atom tables and residue mapping.** For each structure we freeze two tables: an *atom table*
of every atom record of the file, with its chain and residue in author and in label
numbering, and a *mapping table* with the SIFTS correspondence [8, 29, 30] between each residue and its UniProt position. Files are read with GEMMI
[31]. Generators and graders read only these tables; nothing is fetched while a
task is built, graded or loaded.

### 3.2 From data to a task: the running example

The clinical generator produced the running example in six steps.

1. **Variant.** From the pool it picks the *LYZ* variant p.W82R
   (UniProt P61626). Through UniProt's cross-references we found
   2 ClinVar records of this change, both classified as
   pathogenic (SI Section S1).
2. **Structure.** The panel entry for this protein is 2NWD, human lysozyme.
3. **Mapping.** The mapping table says that UniProt positions
   19–148 are author residues
   1–130 of chain X: an offset of
   18, the length of the signal peptide that the cell cuts off. Position
   82 is therefore author residue 64.
4. **Identity check.** The atom table must hold, at that residue, the amino acid that the
   UniProt sequence has at the position; otherwise the variant is not offered for this
   entry. Here it does: Trp64 (the tryptophan at author residue
   64; residues are written in this way below), with
   24 atom records (14 non-hydrogen atoms and
   10 hydrogens, which this entry includes at its high resolution of
   1.04 Å).
5. **Wording.** A seeded random choice picks one of the template's wordings, the colour
   (yellow) and the representation (spacefill spheres). The request never says which residue
   of the entry is meant.
6. **Reference, twice.** The script writes the reference scene (chain X,
   author residue 64, yellow spacefill spheres) and the reference call list
   (load the entry; draw UniProt P61626 position 82 as
   yellow spacefill spheres). The 82 is correct there: the call-list
   viewer can select by UniProt position and converts it itself, which a scene cannot do
   (Section 3.4). Both references must resolve to the same 24 atoms,
   which are stored as the target of both tasks.

The reference contains only what the request states: one residue, one representation, one
colour, and no cartoon of the protein behind it. Section 6.6 shows why this rule exists. On
the call-list track the task also accepts the residue's segment of the default cartoon
recoloured (SI Section S1).

### 3.3 Eight categories of task

Tasks are grouped into eight *categories* (Figure 2, Table 1). Four differ in what the model
must know beyond the request: nothing (*translation*), what the structure contains
(*structure-grounded*), which entry holds a protein (*name resolution*), or which residue
number a variant has in the structure (*clinical variant*). In the last two, the *lookup
categories*, the missing piece is one that a person would look up in a database and that the
model must recall. The other four differ in the form of the task: *interactions*,
*follow-up turn*, *several right answers* and *viewer settings*; Table 1 says what each
asks. Each category has several *templates*; a seeded generator fills in the structure, the
residues, the colours and the wording (SI Section S2 lists the 129
templates, and SI Section S10.2 describes each category in full).

![**Figure 2. The eight categories of task, with one request each.** Counts are tasks on the scene track / the call-list track; a dash means that the category has no task on that track. Requests are quoted from the corpus; a long one is cut short. A grey line under a request explains a term in it. Left column: the four categories that differ in what the model must know. Right column: the four that differ in the form of the task. Framed in blue: the two lookup categories.](generated/fig_tiers.svg)

**Table 1. The corpus.** Tasks per category and track, written as total (a + b): a tasks on the
63 other structures and b tasks on the
15 *set-aside structures*, which the first version of the
benchmark never used (Section 3.6). *Pairs*: requests posed on both tracks. The call-list
track has more translation tasks: 116 exercise calls
that no scene can express. A dash means that the category has no task on
that track: the format cannot express what is asked or, for name resolution, an answer
may sit on an entry outside the panel, which the scene grader can compare as text (Section
4.1) but on which a call list cannot be replayed.

| Category | What is asked | Scene track (other + set-aside) | Call-list track (other + set-aside) | Pairs |
|:---------|:----------------|-----:|-----:|--:|
| ***Differ in what the model must know*** | | | | |
| Translation | Everything needed is in the request; write it in the format. | 73 (55 + 18) | 178 (138 + 40) | 62 |
| Structure-grounded | The request names a feature (the ligand, a bound small molecule; the disulfides, bonds between two cysteines); the model must know which atoms these are. | 63 (52 + 11) | 63 (52 + 11) | 63 |
| Name resolution | The structure is named by protein, not by identifier. | 39 (32 + 7) | – | – |
| Clinical variant | A variant is named in UniProt numbering or in mature-protein numbering; its residue must be found in the structure, where its number often differs. | 82 (63 + 19) | 82 (63 + 19) | 82 |
| ***Differ in the form of the task*** | | | | |
| Interactions | Named atoms and a measurement or contact between them. | 40 (32 + 8) | – | – |
| Follow-up turn | A start state plus an edit request; the full new state is returned. | 58 (50 + 8) | 44 (34 + 10) | 36 |
| Several right answers | The request leaves one countable thing open; several drawn states are right. | 26 (21 + 5) | 15 (11 + 4) | 15 |
| Viewer settings | A viewer setting that only the call-list format can express. | – | 34 (29 + 5) | – |
| **All** | | **381** (305 + 76) | **416** (327 + 89) | **258** |

#### 3.3.1 The clinical category

Each track has 82 clinical tasks, on 31 structures. A request names its variant in UniProt numbering, with
the prefix "p.", or, in 13 requests, by a traditional name, in which
case the request says that the name is in mature-protein numbering and what that numbering
leaves out. 46 requests state the UniProt accession, as the
running example does; the other 36 do not, and neither the request nor
the system prompt then says which sequence a "p." position is counted on. A name with "p."
follows the style of the HGVS nomenclature for variants [32, 33]
but is not a complete description in it (SI Section S10.3). In 10 tasks the
request also asks for the helix or strand (two local shapes of the chain) that contains the
residue; these are reported apart (Table 10).

Two yes-or-no properties of a clinical task matter for the results, and they are not the
same property (Table 2).

- **Copying the number** (Box 1) is right in 34 tasks and wrong in
  48. The question of the Introduction is answered on this
  grouping, on the scene track (Section 6.4).
- **Offset.** The target residue has an offset in 59 tasks, by
  1 to 216 residues. This grouping is reported for
  description only.

**Table 2. The two groupings of the 82 clinical tasks, crossed.** *Copying the
number* and *offset* as in Box 1.

| | Copying the number is right | Copying the number is wrong | All |
|:-----------------|---:|---:|---:|
| **No offset**: the target's author number is its UniProt number | 22 | 1 | 23 |
| **Offset**: the target's author number differs from its UniProt number | 12 | 47 | 59 |
| **All** | **34** | **48** | **82** |

With a name in UniProt numbering, copying is right exactly when there is no offset. The
groupings differ only for traditional names: in 12 tasks the
structure is numbered from the mature protein as the name is, so the copied number is right
although the residue has an offset. The one remaining task uses a traditional name on a
predicted structure, which has UniProt numbering. The name is
E6V of haemoglobin beta
(p.Glu7Val; the mature protein lacks the initiator
methionine). The residue has no offset, yet copying the mature-protein number is wrong.
For 7 variants there are two *matched tasks*: the same
variant, named in UniProt numbering, is asked once on a structure with an offset and once on
a predicted structure without one (SI Section S10.3).

### 3.4 The same request in two formats

A wrong answer has two possible causes: the model did not know which atoms were meant, or it
knew and could not write them in the format. One format cannot separate the two. MolBench
therefore poses 258 requests (68% of the
scene tasks) on both tracks, with identical wording and the same target atoms (Figure 3).

The formats differ in kind. A MolViewSpec scene [19] is declarative: a tree that
states what to load, which atoms to select and how to draw them. A call list is imperative:
each call to the PDBe Mol\* viewer (the build of Mol\* of the Protein Data Bank in Europe),
version 3.3.2 [22], changes the default view, so order matters.

The formats also differ in what they demand for a clinical request. The call-list viewer can select a residue by UniProt accession and position and
does the mapping itself; a scene must give author or label numbers. On the call-list side of
a clinical pair, a model can thus be right without knowing any residue number of the
structure. Clinical pairs are
therefore read apart from the others (Section 6.3).

![**Figure 3. One request, two formats, the same target atoms.** The scene and the call list are shown in shortened form; in the scene, "structure model" is MolViewSpec's name for the deposited coordinates and has nothing to do with a language model. Below: for each model, every pair falls into one of four cells by whether each side is right. A side is right when at least 2 of its 3 answers are *target-right*: the requested atoms are marked out exactly (a target score of 1, Section 4.2). McNemar's test compares the two coloured cells, in which the model was right in one format only; Figure 5 uses the same two colours.](generated/fig_twins.svg)

Pairs exist in five categories (Table 1). In 15 pairs the request asks for something to be shown alone
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

MolBench tasks have been public since May 2026, when a *first version* of the benchmark
was released (Section 6), so a model released later may have seen
earlier ones. Before generation, 15 structures that the
first version had never used were set aside, and the 165 tasks on them
(21% of the corpus) are reported apart as the *set-aside split*.
The split asks one thing: do models score higher on structures that earlier MolBench tasks
used? The test is weak: only
23 of the 63 other
structures appeared in any task of the first version (its pilot run, of scene tasks alone,
used 14 structures), nearly all tasks in both parts are new, and the
split's tasks are public too (Section 9).

To measure sensitivity to wording, 30 requests
(41 tasks, because 11 of them are
pairs) also exist in
a *terse* and an *indirect* wording with the same reference; these task files are not
counted in Table 1 (SI Section S10.6).

### 3.7 Checks on the corpus

Four checks involve no model (Figure 1, lower half): each reference against its structure,
the atom tables against the running viewers, the grader against a control set, and every
task file against the written task format. Section 4.5 reports the second and third. The
run does not start unless every check passes.

## 4. Grading on drawn state

The grader turns the reference and the answer into what the viewer would draw and compares
the two. SI Sections S4 and S11 give every rule.

### 4.1 From an answer to a drawn state

A *style* is one representation with one colour and one opacity, for example "grey cartoon,
opaque". The *drawn state* of an answer is, for every atom of the structure, the set of its
styles, plus a few things about the scene as a whole: text labels, distance lines, the atoms
that the camera is centred on, and viewer settings such as the background colour. The
grader computes it from the frozen atom tables and from the rules of the viewer itself,
which we read back from the running viewer and did not take from documentation. No browser
runs and nothing is fetched while an answer is graded; only the separate check that a
scene is valid, made before grading, runs the viewer (Section 4.4).

The drawn state is cut into *facts* of equal weight. All atoms that carry the same set of
styles form one fact. "The protein as a grey cartoon, with one residue also as red
ball-and-stick" is two facts: the atoms of that residue, and all other protein atoms. Each
label, each distance line and each setting that differs from the default is a further fact.
Atoms that are not drawn belong to no fact.

On the call-list track the grader replays the calls in order, as PDBe Mol\* 3.3.2 would
execute them. Because that viewer draws the whole structure as soon as it loads, the facts
of a call list are its *changes from the default view*.

One category is a partial exception to grading on drawn state. A name-resolution task accepts any PDB
entry of the named protein (5,778 entries over the
39 tasks), and we hold atom tables only for panel entries. For an
answer on an accepted entry outside the panel the grader has no atoms to resolve, so it
compares the answer's selections with the reference's as text; a correct selection that is
spelled differently (by chain identifier, for example) fails. We call this the *text
rule*. An answer on an entry that the task does not accept scores 0 (Table 8).

### 4.2 Three scores

**Task success: is the drawn state exactly right?** For one answer, task success is yes or
no: yes if every fact of the reference is fully present and the answer has no other. The
*task success rate* of a model is the share of its answers that succeed.

**Target score: are the requested atoms marked out exactly?** The *target* of a task is the
atoms that the request is about: in a clinical task, the residue of the variant; in a
request for a feature against a background ("grey cartoon and the biotin in green
ball-and-stick"), the feature; where there is no such distinction, everything that the
reference draws. The target score, from 0 to 1, is how exactly the answer marks out the
target. It is 1, and the answer is *target-right*, when three things hold: the target
atoms carry the requested style; no other atom carries that style; and no second
representation is drawn on target atoms alone. Any other drawing, such as a cartoon of the
protein, is ignored.

The target score is the harmonic mean of a recall and a precision, counted in *items* (one
style on one atom). Recall is the share of the requested items that the answer has, with
half credit for the right representation in another colour or opacity. Precision depends
on what the answer drew beyond the request, which is of three kinds (rows of Table 3 in
parentheses).

- *Spill*: the style that marks the target, repeated on atoms outside it
  (S7, S8). It lowers precision.
- *Extra*: another representation drawn on target atoms alone (S9:
  24 credited items of 48 drawn, precision
  0.50). It lowers precision.
- *Unrequested context*: any other style that reaches beyond the target, such as a cartoon
  of the protein (S5, S10). It is not
  counted.

Precision divides the credit counted for recall by everything that the answer drew to mark the
target: its items of the requested representation on the target, plus its spill and extra
items (formula in SI Section S4.3).

The line between extra and context is a convention, and its consequence may surprise:
ball-and-stick added to the target residue alone lowers the target score to
0.67 (row S9), while the same ball-and-stick on
the residue and its two neighbours is context and leaves the score at
1.00 (row S10; SI Section
S11.3 gives the reason). 31 follow-up tasks, among them
both sides of 8 pairs, have no target score and are left out of every mean of it: their
edit takes something away, changes a setting of the whole view, or needs no change, so no atoms
are "drawn as asked" afterwards (SI Section S11.3).

**F1: how much of the drawn state is right?** F1, from 0 to 1, gives partial credit. It is
the harmonic mean of *recall*, the mean over the facts of the reference of the fraction
that the answer also draws, and *precision*, the same over the facts of the answer. A style
with the right representation and the wrong colour or opacity counts half. On the call-list track each changed
atom is compared by its final appearance as a whole. This is more generous than the scene
rule: any change to the right atoms earns one half, even in the wrong representation, which
earns nothing on the scene track (SI Section S11.2). Where a task lists several accepted answers, an answer is graded against each, and
the best result counts.

**Which score is primary.** Within a track, the primary score is the task success rate,
strict (Section 4.4), because a viewer scene is either the one that was asked for or it is
not. Between the two formats (Table 9a) and for copying against mapping (Table 10), it is
the target score. F1 is reported for partial credit and is never primary. The target score
is used between the formats because task success and F1 are not the same tests on the two
tracks. On
the scene track the screen starts empty, so anything drawn beyond the request costs
precision and task success. On the call-list track only changes from the default view are
graded, and leaving the default view in place costs nothing. Track totals are therefore not
compared on these two scores; the target score is computed with the same counts on both
tracks.

### 4.3 The running example, graded

Figure 4 and Table 3 grade several answers to the running example. The reference draws
Trp64 of chain X as yellow spacefill spheres, and
nothing else.

![**Figure 4. Drawn-state grading of the reference and two answers to the running example.** Top: the three drawings as Mol\* 5.9.0 renders them, from one camera. The reference and Answer A look equally plausible: nothing in either picture says which residue it is. Below, each panel shows a stretch of chain X in author numbering, the facts of the drawn state, and the scores. *Fact*: all atoms that are drawn in the same way. *Recall*: for each fact of the reference, the fraction that the answer also draws, averaged over those facts. *Precision*: the same for the facts of the answer. *F1*: the harmonic mean of recall and precision. *Task success* and *target score* as in Table 3; the target score ignores the cartoon of Answer B.](generated/fig_grading.svg)

**Table 3. Answers to the running example and their scores**, computed by the benchmark's
grader. *F1* (0 to 1): how much of the drawn state is right. *Task success*: the drawn
state is exactly right. *Target score* (0 to 1): how exactly the answer marks out the
requested atoms; any other drawing, such as a cartoon of the protein, is ignored. *Spill*,
*extra on the target* and *context*: the three kinds of drawing beyond the request (Section
4.2).

| Row | Answer | F1 | Task success | Target score |
|:--|:------------------------------------------|--:|:--|--:|
| | **Scene track** | | | |
| S1 | Reference: author chain X, author residue 64, yellow spacefill spheres | 1.00 | yes | 1.00 |
| S2 | The same residue named by label numbering (label chain A, residue 64; in this entry only the chain name differs from the author numbering) | 1.00 | yes | 1.00 |
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

Three points follow. First, an answer may name the residue in any numbering: rows
S2 and C2 are written differently from the reference
and draw the same atoms, so they score the same. Second, the answer that copies the
"82" of p.W82R (rows S3 and
C3) draws Ser82, shares no atom
with the reference, and receives 0 on all three scores. Third, the answer that finds the
right residue and adds a grey cartoon of the protein (row S5) has a
target score of 1.00 but an F1 of 0.40 and no
task success. That F1 alone does not say what went wrong (the right residue drawn red
scores 0.50, row S4); the target score says that the
residue is right and the loss is unrequested context (SI Section S11.4 works every score by
hand).

### 4.4 Valid, unshowable and schema-breaking answers

An answer is *valid* if it obeys the answer format and the viewer can show it. On the scene
track this is decided in a separate step before grading: the scene must pass the validation
of Mol\* 5.9.0 itself, run in a browser without a display, and must name a structure file
that can be loaded, which is decided from the address alone, with nothing fetched. On the
call-list track a valid answer is a JSON list in which every call is documented in the
format guide, has its required fields, and gives each field a value of the documented
kind. An invalid answer is
one of two things. An *unshowable* answer cannot be shown at all:
it holds no parseable JSON of the right outer shape (a scene, or a list of calls) or, on the
scene track, is rejected by the viewer or names a file that cannot be loaded. It scores 0 on
all three scores. A
*schema-breaking* call list breaks that rule (an unknown call, a missing field or a wrongly
typed value, for example). The viewer
ignores such parts and carries on, so the list is graded as the viewer would treat it, but
it is not counted as valid (SI Table S5).

Scores are averaged in three named ways. *Strict*, the default: every answer counts, which
is what a user of a model without tools would experience. *Valid-only*: the mean over a
model's valid answers, which separates "wrote a loadable answer" from "the answer is
right". *Repaired*: strict, after an offline library [34] has repaired each answer that is
not parseable JSON; it never replaces the strict score.

### 4.5 How well the grader itself works

A grader on drawn state can still reject a correct answer that is written in an unexpected
way, or pass a wrong one. We test this with a *control set* of
2,175 controls (Table 4). A control is a reference and one answer whose verdict
is known from how the answer was made: the reference itself (*identical*), the reference
rewritten so that the viewer shows the same (*equivalent*; label numbering in place of
author numbering, for example), or an answer that shows something else (*wrong*; the
UniProt number used as the author number, for example). A *false pass*
is a wrong answer graded as a task success. A *false fail* is an identical or equivalent
answer graded as not a success.

**Table 4. Error rate of the grader on the control set.** *False pass* and *false fail* as
defined above, each out of all answers of its kind. *Earlier grader*: our own grader that this
work replaces on each track; both compared the text of answers. The
four entries that hold only DNA or RNA have no call-list
control, because each call-list control is built around a protein residue (SI Section S5).

| Track | Controls | Structures | Kinds of equivalent / wrong answer | False pass | False fail | Earlier grader: false pass | Earlier grader: false fail |
|:---|---:|---:|---:|---:|---:|---:|---:|
| Scene | 1,155 | 78 | 25 / 26 | 0 of 505 | 0 of 650 | 16 of 505 (3%) | 284 of 650 (44%) |
| Call list | 1,020 | 74 | 22 / 23 | 0 of 445 | 0 of 575 | 95 of 445 (21%) | 319 of 575 (55%) |

The grader makes no error on the control set, and this must be read with care. We developed
the grader against the controls and corrected it until it agreed with every one. The zeros
show that the stated rules are implemented and stay implemented, since the control set is
run as a test on every change. They do not estimate how often a way of writing an answer
that we did not foresee is misjudged. Finding such cases needs people, and is the purpose of
the rating study (Section 5.5).

**Agreement with the viewers.** On the scene track, the
reference and the answer of 910 controls were each loaded in
Mol\* 5.9.0 and read back: the viewer always agreed with the verdict of the control and
drew the atoms that the grader resolves. On the call-list track, a sample of
150 controls holds 300 call
lists (a reference and an answer each). Of these, 267 were
replayed in PDBe Mol\* 3.3.2, and every one ended in the state that the grader computes;
the other 33 were not replayed
(27 of them select by UniProt number), so none
disagreed. Also not checked in a viewer: controls of kinds that cannot be read back (the
text of a label, for example) and call-list controls outside the sample (SI Sections S5
and S11.6).

### 4.6 What is deliberately not graded

Camera coordinates, sizes, line widths and the appearance of labels are not graded; a
requested focus is graded by which residues the camera frames. Colours and opacities are
compared within a small tolerance, under which no colour of the request palette can pass
for another (SI Section S11.7).

## 5. Experimental setup

One run fills every result in Sections 6.1 to 6.5. Its plan is fixed in a single manifest
file before any model is called (SI Section S6). SI Section S12 gives this section in full.

### 5.1 Models

The models are chosen by a written rule, not by results. The 16 *core
models* are those shown in the first version's online results browser in October 2026
(Section 12), taken over unchanged, so that the choice depends on no result of the present
benchmark; 15 of them are in the pilot run of Section 6.6, and the
other could not be reached on the day of that run (SI Section S12.1). Most are the
smaller, cheaper models of their providers. 13 have *open weights* (the
weights can be downloaded) and 3 have *closed weights* (the model can
be used only through a provider's service). Up to 5 *optional
models* (the largest current models of several providers of closed weights, and the largest
model with open weights) are named in the manifest and marked † in the tables; which of them are run is decided from the projected cost alone, before any
result exists. SI Table S7 lists every model with its price.
⟦PENDING: Dan — which of the optional models are run⟧

Two scripts that use no model are run on both tracks as floors. The *keyword script* maps
words of the request to fixed answers. The *literal script* writes what the request spells
out and uses every number as written, as an author residue number. It looks nothing up, so
the difference between a model and the literal script is what the model adds to the words
of the request. On a clinical task it copies the number (Box 1), so its rows show what
copying alone scores.

### 5.2 Prompting conditions

In each condition of Table 5 a model receives a system prompt and the request, and returns
one answer. Both system prompts say that the answer is judged by what the viewer ends up
showing; the scene prompt adds that anything drawn that was not asked for counts against the
answer.

**Table 5. Prompting conditions.** All main results come from the *main* condition. *Format
guide*: a frozen text in the system prompt that documents the answer format. *JSON mode*: a
provider option that forces syntactically valid JSON. *Grounding pack*: the result of an
offline lookup, appended to the request.

| Condition | What the model is given | Run on | Answers per task |
|:-----|:----------|:----------|--:|
| **Main** | A short instruction, the rule for the answer ("answer with one JSON value and nothing else") and the format guide | all models, all tasks, both tracks | 3 |
| Main + JSON mode | The same, with JSON mode switched on | every model that offers JSON mode (15 of the 16 core models, and each optional model that is run); all tasks, both tracks | 1 |
| Main + grounding pack | The same, with the task's grounding pack appended to the request | all models; the lookup categories, scene track | 3 |
| No format guide | The instruction and the rule for the answer only | 3 models; all tasks of the scene track | 3 |

The format guide is all that a model is told about the answer format. The guide of the
scene track documents selection by author and by label numbering; the guide of the
call-list track documents these and selection by UniProt position. Neither says how a given
structure is numbered. No prompt was tuned on benchmark tasks (SI Sections S7 and S12.2).

A grounding pack never contains a scene, a colour or a representation. For a clinical task
it contains the mapped residue, and for a name-resolution task a list of entries. This
condition therefore shows the most that a perfect lookup tool could add; it does not test
whether a model can use raw lookup tables.

### 5.3 Sampling

Each model answers each task three times in the main condition, at the
provider's default temperature, with a limit of 8,000 tokens per answer
(more for models that first write hidden reasoning). An answer that reaches the limit is
*cut off* by the provider. A cut-off or invalid answer is scored as it stands and is not
retried.

### 5.4 Statistics

**Scores and intervals.** A per-model score is the mean over tasks of the mean over the
task's 3 answers (valid-only scores pool a model's valid answers); a mean
over models covers the core models and the optional models that were run, and leaves the
two scripts out. Intervals
are 95% bootstrap intervals [35] with 10,000 resamples.
Whole structures are resampled, not single tasks, because tasks on one structure share its
difficulties. Models are treated as fixed, so an interval describes these models and not
models in general.

**Paired comparison of the formats.** For each model and pair, a side is right when at least
2 of its 3 answers are right. In the primary comparison (Table 9a) an answer
is right when it is target-right, which is the same test in both formats; it covers the
250 pairs that have a target score. The secondary comparison
(Table 9b) uses task success, on all 258 pairs. The two counts of pairs
that are right on one side only are compared with McNemar's exact test [36], one
test per model. The test treats pairs as independent although several sit on one structure,
so we read its p values as descriptions and give beside them the difference of the two
counts with a resampled interval.

**The central clinical comparison.** On the scene track, clinical tasks in which copying the
number is right are compared with those in which it is wrong, on the target score, because
task success also falls when an answer adds unrequested context (difference row of Table
10).

**Six further planned comparisons** are the rows of Table 12, each a difference in task
success rate with an interval: the set-aside split, the two alternative wordings, JSON mode, the
grounding pack and the format guide. We do not correct for multiple comparisons, and we
report every count.

### 5.5 Human check of the grader

After the run, volunteers will check the grader's verdicts against pictures. A rater sees the request and
four pictures from one camera: the reference and a model answer, each drawn whole and each
zoomed on the target atoms. The rater says "same", "different" or "can't tell" twice: on
the whole scenes (compared with the grader's task success) and on the zoomed pictures
(compared with a target score of 1).

The study has 300 such comparisons of valid scene-track answers,
100 for each verdict of the grader (task success; target-right but not a
success; neither), each rated by two raters. We will report how often people call the grader's task
successes the same and its other answers different, the same for the target score, and the
agreement between raters as the yardstick. The call-list track and the name-resolution category are left out (SI Section
S12.5). 

### 5.6 Reproducibility

One command performs the run from the manifest, and one rebuilds this paper from the
archived answers. A *connection test* of the run script on a few tasks, before the corpus was
frozen, exposed faults of the grader, which were corrected; it produced no result reported
here (SI Section S6.1).

## 6. Results

The only results that exist today come from the *first version* of the benchmark: the
corpus and the two text-comparing graders that were public from May 2026 until the present
corpus replaced them. Its run of the scene tasks in October 2026 is the *pilot run*, whose
results are kept apart in the box of Section 6.6. Sections 6.1 to 6.5 show the tables that
the final run will fill; their layout and captions are fixed, and a script fills the cells.
Figure 5 shows the layout of the summary figure.


![**Figure 5. Layout of the result figure that the final run will fill (no data shown).** **A**: task success rate (the share of answers whose drawn state is exactly right) per model, strict, with 95% intervals, one plot per track. The two plots must not be compared with each other (Section 4.2); formats are compared in panel B only. **B**: for each model, its 250 pairs that have a target score, by which side was right (at least 2 of its 3 answers target-right); blue and orange mark the pairs that are right in the scene only and in the call list only, as in Figure 3. **C**: valid answers only, per category: task success rate and target score (0 to 1: how exactly the answer marks out the requested atoms; any other drawing is ignored). A target score well above the task success rate means that the requested atoms were right and something else was not. Panel A is strict and panel C is valid-only, so the two must not be compared.](generated/fig_result_shapes.svg)

### 6.1 Models on both tracks

Tables 6 and 7 give one row per model, one table per track.

**Table 6. Scene track, main condition.** One row per model; † marks an optional model.
*Valid answers*: share of
answers that parse and that the viewer accepts. *Task success rate*: share of answers whose
drawn state is exactly right. *Target score* (0 to 1): how exactly the answer marks out the
requested atoms; any other drawing is ignored. *F1* (0 to 1): how much of the drawn state
is right. *Strict*: every answer counts, an unshowable one as 0. *Valid-only*: the mean over
the model's valid answers. *All-3
rate*: share of tasks on which all 3 answers are exactly right. *Cost*: US
dollars for all calls of the model in this condition, at list price. Scores will carry 95%
intervals (structures resampled).

| Model | Weights | Valid answers | Task success rate, strict | Target score, strict | F1, strict | Task success rate, valid-only | Target score, valid-only | All-3 rate | Cost (USD) |
|:-------|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| Keyword script (no model) | – | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Literal script (no model) | – | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| claude-haiku-4-5 | closed | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| … 15 further rows for the other core models and up to 5 for the optional models (SI Table S7) | | ⟦PENDING: final run⟧ | | | | | | | |

**Table 7. Call-list track, main condition.** Columns as in Table 6, except that a *valid
answer* is a JSON list that keeps to the documented calls, and a schema-breaking
call list keeps, under *strict*, the scores it earns when replayed (Section 4.4).

⟦PENDING: final run — the table for the call-list track, in the shape of Table 6⟧

### 6.2 Categories

**Table 8. Scores by category and track**, mean over the models. *Structures*: the number of
structures under the tasks of the row, which are the units resampled for its intervals.
Scores as in Table 6. The two rows marked *of which* divide the answers of the
name-resolution category by the entry that the model chose (Section 4.1); they are sets of
answers, so they have no number of tasks. An answer on an entry that the task does not
accept, or that loads none, scores 0 and is in the category row only.

| Category | Tasks | Structures | Task success rate, strict | Target score, strict | F1, strict | Task success rate, valid-only | Target score, valid-only |
|:------------------------|---:|---:|---:|---:|---:|---:|---:|
| **Scene track** | | | | | | | |
| Translation | 73 | 67 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Structure-grounded | 63 | 55 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
| Name resolution | 39 | 39 | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
|  *of which:* answers on the reference entry | – | – | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
|  *of which:* answers on another entry that the task accepts (graded by the text rule of Section 4.1) | – | – | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ | ⟦PENDING: final run⟧ |
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

**Table 9. Paired comparison of the two formats.** For each model, its pairs fall into four
cells. A side is *right* when at least 2 of
its 3 answers are right. *Table 9a* (primary): an answer is right when it is
target-right (a target score of exactly 1, Section 4.2), which is the same test in both
formats.
*Table 9b* (secondary): an answer is right when it is a task success, which is not the same
test in the two formats (Section 4.2). An unshowable answer is not right. *McNemar p*: exact
test that the two one-sided counts are equal. *Difference*: pairs right in the scene only
minus pairs right in the call list only, as a share of the pairs, with a 95% interval
(structures resampled).

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

Where both formats demand the same knowledge, a pair that is target-right on one side only
points to the format, and a pair that is wrong on both sides is a candidate for an error of
content. Clinical pairs must be read differently: there a right call list does not show
that the model knew the residue, because the viewer can do the mapping (Section 3.4). The
counts without the clinical pairs are the cleaner test of the formats.
⟦PENDING: final run — the same counts without the clinical pairs, and without the 15 pairs whose reference call list switches off part of the default view (Section 3.4); and, in the SI, the one-sided pairs divided by whether the side that was not right was unshowable⟧

### 6.4 Clinical variants

**Table 10. Clinical tasks on the scene track, grouped by whether copying the number is
right.** On this track the model must map the number itself. *Target score* (the primary
score of this table) and *task success rate* as in Table 6; both are strict means over the
models. *With grounding pack*: the mapped residue is
appended to the request. The rows labelled *Copying the number* and *Offset* are the two
groupings of the same 82 tasks (Table 2, Box 1); the last three rows are subsets. *Matched tasks*: the same variant asked
on a structure with an offset and on a predicted structure without one (descriptive only).
*Helix or strand requested*: Section 3.3.1.

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

This table will answer the question of the Introduction. Four patterns are possible in its first two rows. We state them
before the run and do not predict which one a model will show.

1. *Copying.* The target score is high where copying is right and low where it is wrong.
2. *Mapping.* The target score is high in both rows.
3. *Always converting.* The target score is low where copying is right and high where it is
   wrong: the model changes the number in every case, also where the structure is numbered
   as the request is.
4. *Neither.* The target score is low in both rows, and the loss lies elsewhere.

Only pattern 2 shows that a model knows how each structure is numbered. With the grounding
pack, patterns 1 and 3 should both turn into pattern 2. The patterns describe one model: in
a mean over models, a mixture of copying and converting models could pass for pattern 4, so
the question is answered model by model (SI Section S9). For each model we report the two
row means and the interval of their difference (copying right minus copying wrong). An
interval above zero points towards pattern 1 (score is lost where copying is wrong), and one
below zero towards pattern 3. An interval that includes zero leaves patterns 2 and 4, which
differ only in the level of the two rows; we give the levels and set no threshold between
them.
⟦PENDING: final run — the number of models with an interval above, below and across zero, with the levels of the two rows, from the per-model rows of SI Section S9⟧

### 6.5 Follow-up turns, several right answers, planned comparisons

Table 11 divides the follow-up turns by whether the edit needs a change; Table 12 holds the
planned comparisons of Section 5.4.

**Table 11. Follow-up turns and requests with several right answers.** *Task success rate*:
share of answers whose drawn state is exactly right (for a request with several right
answers: equal to any one of the accepted answers), strict, mean over the models. A
follow-up turn *needs no change* when the start state already shows what is asked; the
right answer returns it unaltered. The two tracks stand side by side for reference; their
task success rates must not be compared (Section 4.2).

| Group | Scene track: tasks | Scene track: task success rate | Call-list track: tasks | Call-list track: task success rate |
|:----------|---:|---:|---:|---:|
| Follow-up turns that need a change | 48 | ⟦PENDING: final run⟧ | 36 | ⟦PENDING: final run⟧ |
| Follow-up turns that need no change | 10 | ⟦PENDING: final run⟧ | 8 | ⟦PENDING: final run⟧ |
| Requests with several right answers | 26 | ⟦PENDING: final run⟧ | 15 | ⟦PENDING: final run⟧ |

**Table 12. The six further planned comparisons of Section 5.4.** Each row compares the task success
rate (strict, mean over the models) between two groups of tasks or two conditions, with a
95% interval on the difference (structures resampled). The conditions are those of Table 5;
the one JSON-mode answer to a task is set against the mean of its 3 main
answers. *Both tracks* means that the tasks of the two tracks are pooled.

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

### 6.6 Preliminary evidence from the first version (pilot run, October 2026)

<div class="box">

**Everything in this box is preliminary.** The pilot run of 18 October 2026 had
15 of the 16 core models, 70 scene tasks
on 14 structures, and one answer per task. None of its tasks is in
the corpus of Section 3. Its archived answers are graded here with the present grader
against the references of that time. The numbers can show patterns; they cannot rank the
leading models.

**Finding 1: whether the answer was valid decided the ranking.** Of 1,050
answers, 75% were valid scenes. Per model the share ranged from
9% to 99%, and strict F1 from
0.07 to 0.84; the two are nearly proportional
(SI Table S21). Valid-only, the models are much closer (F1 from 0.78 to
0.95). Most invalid answers were not parseable JSON, often with
unbalanced braces: a scene is a deeply nested tree, and one brace too many loses the whole
answer. This is why the final run reports strict and valid-only scores together and adds a
JSON-mode condition.

**Finding 2: clinical tasks lost their points on unrequested context, not on the residue.**
The clinical category scored lowest: strict F1 0.31, and task
success in 5 of 135 answers (Figure 6).
The natural reading is that finding the residue of a variant is hard. That reading is wrong
for this run. In 64% of the 135
clinical answers, and in 91% of the valid ones,
the requested residue
was drawn exactly as in the reference. The points were lost elsewhere: each clinical
reference also drew a grey cartoon of the whole protein, and the requests asked only for
the residue. There was a second error. All 9 clinical
tasks used a single structure in which author numbers equal UniProt numbers, so the
category could not test the mapping at all. "Most answers drew the right residue" is
therefore a statement about drawing, not about mapping.

![**Figure 6. Pilot run: three scores by category (preliminary).** All three are on a scale from 0 to 1 (0.70 is 70% of answers; SI Table S22 gives the numbers). *F1* (how much of the drawn state is right) and *task success* (the share of answers whose drawn state is exactly right) are strict, over all answers of all 15 models; an unshowable answer scores 0. *Requested part exactly right*: among answers to tasks whose reference marks out a requested part against a background, the share that draw that part exactly as the reference does, whatever the rest of the answer shows. It is the forerunner of the target score; the pilot tasks stored no target. The number of answers behind each bar is printed above it (n). Three categories with few tasks are pooled in the middle group. In the clinical category the requested part was usually right and the whole drawn state almost never.](generated/fig_october_regrade.svg)

**Further findings** rest on other conditions of the pilot run and on a separate run of
the first version's call-list tasks in July 2026 (SI Section S13.1, Findings
3 to 6). Grounding packs did not help, which
Finding 2 explains: the residue was already right without them. Without the format guide,
none of 420 answers was a valid scene. In the call-list run, a keyword
script reached a mean F1 of 0.72 where the models scored
0.72 to 0.95, which is why that track was
rebuilt. And a trial of the rating study with three raters
was too small to validate anything.

</div>

## 7. Errors in the first version and their corrections

The first version of MolBench was wrong in nine ways that we know of. Table 13 names each
error and what replaced it, because each is one that another benchmark of this kind could
make. SI Section S13.2 says how each was found.

**Table 13. Nine errors in the first version of MolBench and what replaced each.**

| | What was wrong | What replaced it |
|--:|:----------------|:----------------|
| 1 | Clinical references drew a cartoon that no request asked for, and we read the low score that followed as a difficulty of finding the residue. | A reference holds only what the request states. Every task stores its target where it has one, and the target score is reported beside task success. |
| 2 | The clinical category could not test the mapping: all its tasks sat on one structure that uses UniProt numbering. | 82 tasks on 31 structures; copying the number is wrong in 48 of them, and results are grouped by that property. |
| 3 | "Pathogenic" was taken from a secondary source, UniProt's variant annotation. | A variant is used only if a ClinVar record of that gene and that one change is classified as pathogenic or likely pathogenic with stated criteria (one exception, lysozyme p.Ile74Thr, whose record states no criteria; Section 3.1). |
| 4 | Both graders compared text. They rejected correct answers that were written differently (44% and 55% of them on the control set) and passed some wrong ones. | Both tracks are graded on drawn state, and the control set is run as a test on every change. |
| 5 | Hand-written call-list references had errors, such as label numbers where author numbers were meant. | Every reference is generated and checked against the structure. |
| 6 | Some requests had no single answer ("show me lysozyme"). | Requests with a countable ambiguity list every accepted answer; open-ended requests are left out. |
| 7 | Raters could not see what they were rating: one highlighted residue on a whole complex is a few pixels wide. | Pictures are also framed on the target atoms, from one shared camera. |
| 8 | One answer per task, on 14 structures, with no record of answers that were cut off. | 3 answers per task, 78 structures, and the reason for the end of each answer archived. |
| 9 | The prompts taught answers that the graders marked wrong. | Both prompt examples are graded by the benchmark's own grader as a test. |

## 8. Discussion

⟦PENDING: final run — discussion of the results: which categories separate models, what the paired comparison shows, whether the set-aside split differs from the other tasks, and what Table 10 says about mapping against copying⟧

Two points concern the instrument and can be made before the final run.

**One score is not enough.** The pilot run gave three different pictures of the same
answers. Strict scores mostly measured whether a model returned a scene that the viewer
could load. F1 in the clinical category mostly measured whether a model reproduced a
background. Only a score restricted to the requested atoms showed that the residue was
usually drawn right. We therefore report task success and the target score together.

**A benchmark's references need the same scrutiny as the models.** The most important
finding so far concerns our own references (Table 13, row 1). It was found by asking where
valid answers lost their points, not by looking at totals. We recommend that analysis to
anyone who builds a benchmark with partial credit.

## 9. Limitations

The limits that bound the claims of this paper most are listed here; SI Section S14 gives
the full list with numbers.

- **One viewer per track.** Answers are graded by the rules of Mol\* 5.9.0 and of PDBe Mol\*
  3.3.2. We make no claim about PyMOL, ChimeraX or VMD.
- **A model alone.** A model cannot look anything up, ask a question or see the picture. A
  product that wraps a model in tools, validation and retries may do better.
- **Requests from templates.** They are cleaner than what people type, no independent
  structural biologist has yet read them for naturalness, and open-ended requests ("show
  the active site clearly") are left out.
- **Public tasks.** The whole corpus, set-aside split included, was public before the run,
  so no part of it can show whether a model has memorised tasks.
- **A small panel of well-known structures.** The 79 structures were chosen by
  hand; the median year of deposition is 1999. Scores may be higher
  than on recent or very large structures.
- **ClinVar is a snapshot, read through UniProt.** Classifications change. We looked only at
  the records that UniProt cross-references, did not check which transcript (messenger RNA of the gene) a
  record's protein-level name is counted on, and attach the classification to a protein-level name
  without naming the disease, which ClinVar itself does not do. The residue that a name points to
  does not depend on the classification.
- **The grader is tested only against cases that we foresaw** (Section 4.5). Until the
  rating study is done,
  the evidence that task success matches what people see is the control set and the
  read-back from the viewers. Selections by UniProt position were not replayed in the
  viewer, and name-resolution answers outside the panel are compared as text.
- **Partial credit is a choice.** Equal weight for facts and half credit for a wrong colour
  are conventions, and F1 is not the same measure on the two tracks. Task success does not
  depend on them.
- **The formats are not compared on equal terms everywhere.** The call-list viewer can map a
  UniProt position itself, and the two system prompts differ in length
  (1,328 and 1,556 words).
- **Small groups are descriptive only.** The set-aside split within one category, the
  matched clinical tasks, the helix and strand tasks and the two alternative wordings are reported
  with intervals and not tested. In every set of matched tasks the structure without an
  offset is a predicted structure, so the effect of the offset cannot be told apart from
  that of a predicted structure.

## 10. Conclusion

MolBench grades how a language model drives a molecular viewer on the atoms,
representations and colours that the viewer would draw, without a judge model. References
are computed by script from the structure, the SIFTS mapping and ClinVar. The corpus has 797 tasks on 78
structures, and 258 requests are posed in two answer formats, to
tell errors of content from errors of format. The grader agrees with all
2,175 control answers against which it was developed, and a check by people is
planned. A pilot run
taught two things: most points were lost to answers that the viewer could not show,
and in the clinical category most were lost to our own references, which drew an
unrequested cartoon. In the rebuilt category, copying the number from the variant
name gives the wrong residue in 48 of 82 tasks, and the
final run will show whether models copy it.
⟦PENDING: final run — two sentences on the results: how well the models drive the viewer on each track, and what the paired comparison shows⟧

## 11. Ethics, human participants and licences

**No patient data.** The benchmark contains no data about individuals. Clinical variants come
from UniProt's variant annotation and are confirmed in ClinVar's public variant-level
records (one exception, whose record states no assertion criteria; Section 3.1).

**Not for clinical use.** A high score does not make a model fit to interpret variants. The
clinical category measures whether a model can locate a residue in a structure. The data providers
say the same of their data: UniProt and the AlphaFold Protein Structure Database state that
their content is not a substitute for professional medical advice. ⟦PENDING: Dan — ClinVar's own statement on clinical use, to be read at the source by hand and added to this sentence; the page refuses automated reading⟧

**Volunteer raters.** The rating study asks volunteers to compare pictures of a molecule. It collects their answers, optional free-text notes
and the time taken per item. Raters are identified in the analysis by pseudonyms; no names,
contact details or rater identifiers are published. ⟦PENDING: Dan — confirm the consent wording shown to raters, and whether the target journal or the author's institution requires an ethics statement or a waiver for this study⟧

**Use of language models in this work.** Language models are the subject of the study. They
were also used as coding and drafting assistants in building the benchmark and in writing
this manuscript. The authors checked all content and are responsible for it.
⟦PENDING: Dan — final wording of this disclosure, which the journal asks for in the Acknowledgements⟧

**Licences of data and software.** Third-party data and software are used under their own
terms, which we read at each source on 16 November 2026 (SI Table S24); frozen copies in the
repository keep those terms. MolBench's own code, tasks and references are released under the MIT licence.

## 12. Data and Software Availability

- **Code, tasks, references, graders, control set:** <https://github.com/dbolser/MolBench>
  (MIT licence). Corpus version `corpus-v1.0`, SHA-256 `45a841aecbd25a72c0d1f9a91704b3031318955bd44300e3bf547ffa95e4edd8`.
- **Archive:** ⟦PENDING: deposit — DOI of the frozen corpus, including the set-aside split, and of the raw model answers and score files of the final run⟧
- **Rating data:** ⟦PENDING: deposit — anonymised ratings of both rating studies, with the analysis scripts⟧
- **Results browser:** <https://dbolser.github.io/MolBench/>.
- **This paper:** every table, figure and number is regenerated by scripts in the
  repository from the task files, the frozen data and the archived answers.

Grading a validated answer needs no network access and no paid service. Validation by the viewer and the pictures
for the rating study need a browser without a display and the Mol\* bundle, both free.

## Supporting Information

The Supporting Information (one PDF file) contains: glossary (S0); running example (S1);
task templates (S2); structure panel and variant list (S3); grading rules (S4); control set
(S5); run manifest, models and connection test (S6); system prompts (S7); tables of the
pilot run and the trial of the rating study (S8); further tables of the final run (S9,
pending); and the long form of Sections 3 to 5 (S10 to S12), of the pilot findings and the
errors of the first version (S13), of the limitations (S14), and of related work and
licences (S15).

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
10. Goddard TD, Huang CC, Meng EC, Pettersen EF, Couch GS, Morris JH, Ferrin TE. UCSF ChimeraX: Meeting modern challenges in visualization and analysis. *Protein Science* 2018;27(1):14–25. doi:[10.1002/pro.3235](https://doi.org/10.1002/pro.3235)
11. Dai D, Qi H, Liu L, Li Y, Chen B, Dou Z, Zeng Q, Kang Q et al. OSWorld-Science: A Benchmark of Computer Use Agents for Learning and Using Scientific Software. *arXiv preprint* 2026. arXiv:[2609.39903](https://arxiv.org/abs/2609.39903)
12. Xie T, Zhang D, Chen J, Li X, Zhao S, Cao R, Toh JH, Cheng Z et al. OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments. *arXiv preprint* 2024. arXiv:[2404.07972](https://arxiv.org/abs/2404.07972)
13. Ai K, Miao H, Tang K, Gorski N, Sun J, Liu G, Ingolfsson HI, Lenz D et al. SciVisAgentBench: A Benchmark for Evaluating Scientific Data Analysis and Visualization Agents. *arXiv preprint* 2026. arXiv comment: IEEE Transactions on Visualization and Computer Graphics (IEEE VIS '26). arXiv:[2603.29139](https://arxiv.org/abs/2603.29139)
14. Qin Y, Liang S, Ye Y, Zhu K, Yan L, Lu Y, Lin Y, Cong X et al. ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs. *arXiv preprint* 2023. arXiv:[2307.16789](https://arxiv.org/abs/2307.16789)
15. Yao S, Shinn N, Razavi P, Narasimhan K. tau-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains. *arXiv preprint* 2024. arXiv:[2406.12045](https://arxiv.org/abs/2406.12045)
16. RenhaoL. molstar-mcp: a Model Context Protocol server that builds MolViewSpec scenes for Mol*. *Software, MIT; repository created 2026-05-31*. <https://github.com/RenhaoL/molstar-mcp>
17. Jia D, Irger A, Besançon L, Strnad O, Luo D, Björklund J, Kouyoumdjian A, Ynnerman A et al. VOICE: Visual Oracle for Interaction, Conversation, and Explanation. *IEEE Transactions on Visualization and Computer Graphics* 2025;31(10):8828–8845. Preprint: arXiv:2304.04083. doi:[10.1109/TVCG.2025.3579956](https://doi.org/10.1109/TVCG.2025.3579956)
18. Cortes Rodriguez F, Abriata L. Speech recognition assisted by large language models to command software orally -- Application to an augmented and virtual reality web app for immersive molecular graphics. *arXiv preprint* 2026. arXiv:[2603.02901](https://arxiv.org/abs/2603.02901)
19. Midlik A, Bittrich S, Fleming JR, Nair S, Velankar S, Burley SK, Young JY, Vallat B et al. MolViewSpec: a Mol* extension for describing and sharing molecular visualizations. *Nucleic Acids Research* 2025;53(W1):W408–W414. doi:[10.1093/nar/gkaf370](https://doi.org/10.1093/nar/gkaf370)
20. Bittrich S, Midlik A, Varadi M, Velankar S, Burley SK, Young JY, Sehnal D, Vallat B. Describing and Sharing Molecular Visualizations Using the MolViewSpec Toolkit. *Current Protocols* 2024;4(7):e1099. doi:[10.1002/cpz1.1099](https://doi.org/10.1002/cpz1.1099)
21. Sehnal D, Bittrich S, Deshpande M, Svobodová R, Berka K, Bazgier V, Velankar S, Burley SK et al. Mol* Viewer: modern web app for 3D visualization and analysis of large biomolecular structures. *Nucleic Acids Research* 2021;49(W1):W431–W437. doi:[10.1093/nar/gkab314](https://doi.org/10.1093/nar/gkab314)
22. PDBe. PDBe Molstar (pdbe-molstar): the PDBe implementation of Mol*, version 3.3.2. *Software, Apache-2.0; version 3.3.2 published on npm 2024-11-25*. <https://github.com/molstar/pdbe-molstar>
23. Smit J, ipymolstar contributors. ipymolstar: Mol* as an anywidget, version 0.1.0. *Software, MIT; version 0.1.0 released on PyPI 2025-04-10*. <https://github.com/molstar/ipymolstar>
24. Vollmar M, Westrip S, Nair S, Balasubramaniyan B, Velankar S, Jones L, Strickland P. Associating protein residues in the literature with structural data. *Acta Crystallographica Section D Structural Biology* 2026;82(2):113–125. doi:[10.1107/S2059798326000021](https://doi.org/10.1107/S2059798326000021)
25. Li Z, Kong X, Su J, Ma Z, Li M, Li S, Zhang Y, Rong Y et al. From Macro to Micro: Benchmarking Microscopic Spatial Intelligence on Molecules via Vision-Language Models. *arXiv preprint* 2025. arXiv:[2512.10867](https://arxiv.org/abs/2512.10867)
26. wwPDB consortium. Protein Data Bank: the single global archive for 3D macromolecular structure data. *Nucleic Acids Research* 2019;47(D1):D520–D528. doi:[10.1093/nar/gky949](https://doi.org/10.1093/nar/gky949)
27. Varadi M, Bertoni D, Magana P, Paramval U, Pidruchna I, Radhakrishnan M, Tsenkov M, Nair S et al. AlphaFold Protein Structure Database in 2024: providing structure coverage for over 214 million protein sequences. *Nucleic Acids Research* 2024;52(D1):D368–D375. doi:[10.1093/nar/gkad1011](https://doi.org/10.1093/nar/gkad1011)
28. Jumper J, Evans R, Pritzel A, Green T, Figurnov M, Ronneberger O, Tunyasuvunakool K, Bates R et al. Highly accurate protein structure prediction with AlphaFold. *Nature* 2021;596(7873):583–589. doi:[10.1038/s41586-021-03819-2](https://doi.org/10.1038/s41586-021-03819-2)
29. PDBe-KB consortium. PDBe-KB: a community-driven resource for structural and functional annotations. *Nucleic Acids Research* 2020;48(D1):D344–D353. doi:[10.1093/nar/gkz853](https://doi.org/10.1093/nar/gkz853)
30. PDBe-KB consortium. PDBe-KB: collaboratively defining the biological context of structural data. *Nucleic Acids Research* 2022;50(D1):D534–D542. doi:[10.1093/nar/gkab988](https://doi.org/10.1093/nar/gkab988)
31. Wojdyr M. GEMMI: A library for structural biology. *Journal of Open Source Software* 2022;7(73):4200. doi:[10.21105/joss.04200](https://doi.org/10.21105/joss.04200)
32. den Dunnen JT, Dalgleish R, Maglott DR, Hart RK, Greenblatt MS, McGowan-Jordan J, Roux AF, Smith T et al. HGVS Recommendations for the Description of Sequence Variants: 2016 Update. *Human Mutation* 2016;37(6):564–569. doi:[10.1002/humu.22981](https://doi.org/10.1002/humu.22981)
33. Hart RK, Fokkema IFAC, DiStefano M, Hastings R, Laros JFJ, Taylor R, Wagner AH, den Dunnen JT. HGVS Nomenclature 2024: improvements to community engagement, usability, and computability. *Genome Medicine* 2024;16(1):149. doi:[10.1186/s13073-024-01421-5](https://doi.org/10.1186/s13073-024-01421-5)
34. Baccianella S. json_repair: repair malformed JSON from LLMs, APIs, logs, and user input in Python. *Software, MIT* 2026. <https://github.com/mangiucugna/json_repair>
35. Efron B. Bootstrap Methods: Another Look at the Jackknife. *The Annals of Statistics* 1979;7(1):1–26. doi:[10.1214/aos/1176344552](https://doi.org/10.1214/aos/1176344552)
36. McNemar Q. Note on the Sampling Error of the Difference Between Correlated Proportions or Percentages. *Psychometrika* 1947;12(2):153–157. doi:[10.1007/BF02295996](https://doi.org/10.1007/BF02295996)
