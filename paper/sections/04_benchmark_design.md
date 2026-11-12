## 3. Benchmark design

This section describes the benchmark as it will be at the final run. Parts not yet built are
tagged. The preliminary results in Section 6 were obtained on an earlier, smaller corpus, which
is described there.

### 3.1 What a task is

A task has four parts:

- a **request** in plain language, as a user would type it;
- a **reference answer** in the output format of its track;
- a **provenance record**: the script that built the reference, the data it read, and the
  structural facts it relied on (for example, "UniProt P04637 position 175 = chain A, author
  residue 175");
- a frozen **grounding pack**: a short block of facts about the structure, used only in one
  ablation (Section 5.2).

The model sees the request and a fixed system prompt. It returns one answer. Nothing is
executed for the model, and it cannot look anything up: the benchmark is closed-book.

### 3.2 Two tracks

**MVS track (headline).** The model writes a MolViewSpec scene: a JSON tree whose nodes download
a structure, parse it, pick components (sets of atoms), give each a representation and a colour,
and optionally add labels, drawn lines or a camera focus [@midlik2025mvs]. A scene is
declarative. It says what should be visible, not how to get there.

**API track.** The model writes an ordered list of calls for the PDBe Mol\* viewer, in the form
exposed by its notebook widget [@pdbemolstar; @ipymolstar]: load an entry, set the global style,
colour or highlight a selection, focus, hide water, and so on. A call list is imperative. Order
matters, and a later call can overwrite an earlier one. The target is fixed at pdbe-molstar
3.3.2, the version that ipymolstar 0.1.0 loads.

For both tracks the format reference is a frozen document stored in the repository. It is shown
to the model, and it is the authority the grader follows.

The API track cannot do everything a scene can, and the reverse. In particular, the PDBe viewer
has no selection by distance or by property and cannot superpose two arbitrary structures. We do
not test those operations in either track.

### 3.3 Regimes of difficulty

A regime is a group of tasks that need the same kind of knowledge. Three regimes form a
gradient:

1. **Translation.** The request states everything: the entry, the chain or residue range, the
   representation, the colour. The model only has to translate. References are built with the
   MolViewSpec builder library [@bittrich2024mvs] from a template and a structure.
2. **Structure-grounded.** The request names a feature and not its location: "the haem", "the
   disulfide bonds". The model must know or infer which atoms that is. References are extracted
   from the deposited file with GEMMI [@wojdyr2022gemmi].
3. **Clinical.** The request names a variant or a residue by its UniProt position, as clinical
   databases do. The model must work out which residue of which chain in the structure that is.
   References are built from the UniProt variant records [@uniprot2025; @landrum2018clinvar] and
   the SIFTS residue mapping [@dana2019sifts], both frozen in the repository.

Two further regimes test other skills and are not steps on the gradient:

4. **Resolution.** The request names a protein and no entry ("show green fluorescent protein").
   Any entry from a frozen list of accepted entries counts as the right structure.
5. **Interactions.** The request asks for specific contacts, such as the hydrogen bonds to a
   ligand, drawn between named atoms. Each atom is checked against the deposited file.

The clinical tier of the preliminary corpus had a weakness that the final corpus removes. All of
its tasks used one structure (1TUP, the p53 core domain), where UniProt numbering happens to
equal author numbering. Those tasks test whether a model picks the right chain. They cannot test
whether it converts a UniProt position to a different author number. The final clinical tier has
⟦PENDING: final count (target: at least 40 tasks on at least 12 proteins, at least 8 of them with
a UniProt-to-author offset)⟧.

### 3.4 Structures

Tasks on the same structure are not independent: a model that knows haemoglobin well gains on
all of them. The final corpus therefore spreads tasks over ⟦PENDING: final structure count
(target: at least 50 PDB entries; the preliminary corpus has {{mvs.n_structures}})⟧, and all
confidence intervals resample whole structures (Section 4.6). For each structure the repository
holds a frozen atom table, a frozen SIFTS mapping and the grounding facts, so grading needs no
network access.

### 3.5 Paired tasks

Every MVS task that the API can express has an API twin: the same request and the same target
atoms. Twins let us compare formats on identical content. For each model and each pair we record
whether each twin was a full success, and we test the difference with McNemar's test for paired
proportions [@mcnemar1947].

Clinical twins are not a clean comparison, and we flag them. The PDBe viewer accepts a UniProt
accession and residue number and does the mapping itself. In the API track a clinical request
can therefore be answered without knowing the mapping. In the MVS track it cannot. We report the
paired analysis with and without clinical twins.
⟦PENDING: number of pairs in the final corpus⟧

### 3.6 Follow-up turns

Real use is a conversation. The second request edits the scene the first one made: "now colour
the ligand red". ⟦PENDING: follow-up tier (target: about 30 two-turn tasks in both tracks)⟧ Each
such task gives the model a starting scene and an edit request. Only the final state is graded,
so a model that carries out the edit and loses an earlier choice (it recolours the ligand and
drops the surface) loses points.

### 3.7 Requests with more than one right answer

Some honest requests are ambiguous. "Show the binding site" does not say how. For a small tier
⟦PENDING: accept-set tier (target: about 15 tasks)⟧ a script builds several accepted final
states, and the task is scored against the best-matching one. We do not use a judge model for
these tasks.

### 3.8 What is not in this benchmark

Open-ended requests that can only be judged by eye ("make a figure that shows why this mutation
matters") are out of scope here and are future work. So are agents that call tools in a loop.
We tested the premise for a tool loop, namely that giving the model looked-up facts raises its
score, and it did not hold (Section 6.4).
