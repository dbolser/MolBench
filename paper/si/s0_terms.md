## S0. Background terms

For readers from outside structural biology. Box 1 of the paper defines the terms of
sequences and variants (UniProt, ClinVar, transcript, missense variant, mature protein,
polymer, ligand, representation) and the main terms of the corpus; Box 2 defines the terms of
grading. Table S0a adds background terms of structural biology, and Table S0b the terms of the
corpus that the paper defines in its text only.

**Table S0a. Background terms of structural biology.**

| Term | Meaning |
|:---------|:------------------------------|
| Residue, chain | A protein is a chain of amino acids. One amino acid in the chain is a *residue*; residues are numbered along the chain. A structure file names each chain with a short identifier, often one letter. |
| C-alpha | The central carbon atom of an amino acid, to which its side chain is attached. One C-alpha per residue traces the course of the chain. |
| Polymer | The protein, DNA or RNA chains of a structure, as opposed to bound small molecules, ions and water. |
| Structure, entry | A set of atom coordinates. An *entry* is one deposition in the Protein Data Bank (PDB), with a four-character identifier such as {{ex.entry}}. A *predicted structure* is one computed from the sequence; ours come from the AlphaFold Protein Structure Database. |
| Coordinate set (PDB "model") | One complete set of atom positions in an entry. An entry solved by nuclear magnetic resonance usually holds several; the PDB calls each a *model* and numbers them (`pdbx_PDB_model_num`). We use the first, and we say *coordinate set* because *model* in this paper means a language model. |
| Assembly | The form in which the molecule is thought to work, for example a pair of identical chains. An entry can deposit one copy and describe how the others are generated from it by symmetry. |
| mmCIF | The file format of the PDB archive: tables of named columns, one row per atom in the table of atoms. |
| Ligand, het group | A *ligand* is a small molecule bound to the protein. *Het group* is the older file term for any molecule in an entry that is not part of a polymer chain (a ligand, an ion, a water); each kind has an identifier of up to three characters, such as HEM for haem. |
| Helix, strand | The two common local shapes of a protein chain. An entry records where each helix and each strand begins and ends. |
| Disulfide bond | A link between the sulfur atoms of two cysteine residues. |
| Representation | A way of drawing atoms: *cartoon* (a ribbon that traces the chain), *ball-and-stick*, *spacefill* (every atom as a full-size sphere), *surface*. |
| Selection | The expression in an answer that picks atoms, for example "chain {{ex.auth_chain}}, residue {{ex.auth_number}}". |
| Alternate positions | The same atom recorded at two or more positions, where the experiment saw a residue in more than one pose (the file calls these alternate conformers). |

**Table S0b. Further terms of the corpus**, each defined in the section of the paper that is
named with it.

| Term | Meaning in the paper |
|:---------|:------------------------------|
| SIFTS | Structure Integration with Function, Taxonomy and Sequences: the public residue-by-residue mapping between PDB entries and UniProt sequences (Section 3.1). |
| Structure panel | The fixed set of {{panel.n}} structures. Tasks are built on {{corpus.n_structures}} of them; one, {{prompt.worked_example_entry}}, is reserved for the worked example of both system prompts (Section 3.1). |
| Category | One of eight kinds of task. The categories are not steps on one scale of difficulty (Section 3.3). |
| Lookup categories | Name resolution and clinical variant. In these the answer needs one fact that a person would look up in a database: an entry identifier, or a residue number. The model cannot look it up and must recall it (Section 3.3). |
| Template | A fixed kind of request within a category; a generator script fills in the structure, the residues, the colours and the wording (Section 3.3). |
| Accepted answer | One of several drawn states that a task lists as right. An answer is graded against each, and the best result counts (Sections 3.3 and 4.2). |
| Held-back split | The tasks on {{corpus.heldback.n_structures}} structures that were set aside before generation and kept out of every earlier MolBench release. The tasks are public; the name does not mean a hidden test set (Section 3.6). |

**Table S0c. Names used in the repository and in the prompts printed in Section S7.** The
paper and this file use the words on the right.

| In the repository or a prompt | In the paper |
|:---------|:------------------------------|
| draw | style |
| tier | category |
| MVS; MVS state, scene tree | MolViewSpec; scene |
| action, canonical action | one call of a call list |
| pdbe-molstar | PDBe Mol\* |
| task identifiers ending in `-mvs` / `-api` | scene track / call-list track |
