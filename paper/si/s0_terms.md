## S0. Glossary and background terms

For readers from outside structural biology, and as the full glossary of the paper. Box 1 of
the paper defines the few terms that carry its results. Table S0a adds background terms of
structural biology, Table S0b the terms of the corpus that the paper defines in its text
only, and Table S0c the names used in the repository. Tables S0d to S0f are the full
glossaries: sequences and variants (S0d), the corpus (S0e), and grading and the run (S0f).

**Table S0a. Background terms of structural biology.**

| Term | Meaning |
|:---------|:------------------------------|
| Residue, chain | A protein is a chain of amino acids. One amino acid in the chain is a *residue*; residues are numbered along the chain. A structure file names each chain with a short identifier, often one letter. |
| C-alpha | The central carbon atom of an amino acid, to which its side chain is attached. One C-alpha per residue traces the course of the chain. |
| Polymer | The protein, DNA or RNA chains of a structure, as opposed to bound small molecules, ions and water. |
| Structure, entry | A set of atom coordinates. An *entry* is one deposition in the Protein Data Bank (PDB), with a four-character identifier such as {{ex.entry}}. A *predicted structure* is one computed from the sequence; ours come from the AlphaFold Protein Structure Database. |
| Coordinate set (PDB "model") | One complete set of atom positions in an entry. An entry solved by nuclear magnetic resonance usually holds several; the PDB calls each a *model* and numbers them (`pdbx_PDB_model_num`). We use the first, and we say *coordinate set* because *model* in this paper means a language model. |
| Assembly | The form in which the molecule is thought to work, for example two identical chains. An entry can deposit one copy and describe how the others are generated from it by symmetry. |
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
| Lookup categories | Name resolution and clinical variant. In these the answer needs one piece of information that a person would look up in a database: an entry identifier, or a residue number. The model cannot look it up and must recall it (Section 3.3). |
| Template | A fixed kind of request within a category; a generator script fills in the structure, the residues, the colours and the wording (Section 3.3). |
| Accepted answer | One of several drawn states that a task lists as right. An answer is graded against each, and the best result counts (Sections 3.3 and 4.2). |
| Set-aside split | The tasks on {{corpus.heldback.n_structures}} structures that were set aside before generation and that the first version of the benchmark never used, in any of its releases. The tasks are public; the split is not a hidden test set (Section 3.6). |
| Qualifying record, best-reviewed record | A *qualifying record* of a variant is a ClinVar variation record, cross-referenced by UniProt, that meets the four conditions of Section 3.1 of the paper. Its *best-reviewed record* is the qualifying record with the highest review status (Section S14.2). |

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
| split `heldback` / `public` | set-aside split / tasks on the other structures |
| legacy name, mature numbering | traditional name, mature-protein numbering |

**Table S0d. Terms of sequences, variants and the viewer.**

| Term | Meaning |
|:---------|:------------------------------|
| UniProt, canonical sequence | UniProt is the reference database of protein sequences. Each protein has an accession, such as {{ex.accession}}, and one sequence that UniProt picks as its reference, the *canonical sequence*. |
| ClinVar | A public archive of human genetic variants. Submitters, mostly clinical laboratories, send their classification of a variant for a condition, on a scale from benign through uncertain significance to pathogenic. For each *variation record* (accession beginning with VCV; usually one change at the level of DNA) ClinVar publishes an aggregate *germline* classification, such as "Pathogenic", and a *review status*. Germline variants are present in every cell of a person, inherited or newly arisen, as opposed to somatic variants that arise in a tumour. The review status says how far the classification has been reviewed (stated criteria, several submitters in agreement, an expert panel); it is not a measure of the strength of the evidence. Different DNA changes can give the same amino-acid change, so one amino-acid change can have more than one record. We write ClinVar's terms in lower case. |
| Transcript | A reference sequence of one messenger RNA of a gene, with an accession and a version number ({{ex.clinvar_transcript}}). ClinVar states each change on a transcript, in the form {{ex.clinvar_cdna}}: nucleotide {{ex.clinvar_cdna_position}} of the coding sequence, counted from the A of the start codon ATG, changes from {{ex.clinvar_cdna_from}} to {{ex.clinvar_cdna_to}}. A gene can have several transcripts, and they can number the protein differently. |
| Missense variant; {{ex.name_in_prompt}} | A change of one amino acid into another. {{ex.name_in_prompt}}: the tryptophan (W) at position {{ex.uniprot_position}} becomes an arginine (R). The same in three-letter form is {{ex.hgvs}}. The prefix "p." marks a description of a change in the protein, as opposed to "c." for the coding DNA; it does not say which sequence the position is counted on. In this paper it is the UniProt canonical sequence, here {{ex.accession}}. HGVS, the nomenclature of the Human Genome Variation Society for naming variants, does not accept a UniProt accession as a reference sequence (Section S10.3). |
| Signal peptide, mature protein, traditional name | The *mature protein* is what is left after the cell has removed the leading part of a newly made protein. That part can be the first residue alone, the *initiator methionine* (haemoglobin beta); a *signal peptide* (lysozyme: {{ex.offset}} residues); or a signal peptide and a further segment, a *propeptide* (coagulation factor IX: {{clin.f9_removed}} residues). Older literature often numbers residues from the first residue of the mature protein; we call a variant name of this kind a *traditional name* (the genetics literature also says legacy name) and its numbering *mature-protein numbering*. A traditional name carries no "p.", as in {{ex.mature_name}}. |
| Mol\*, MolViewSpec | Mol\* is an open-source molecular viewer that runs in a web browser. MolViewSpec is a format, written in JSON (JavaScript Object Notation), that describes what Mol\* should load and draw. PDBe Mol\* is the build of Mol\* maintained by the Protein Data Bank in Europe (PDBe). |
| Polymer, ligand | The *polymer* is the protein, DNA or RNA chains of a structure. A *ligand* is a small molecule bound to them. |
| Representation | A way of drawing atoms: *cartoon* (a ribbon that traces the whole polymer chain, the usual background of a picture), *ball-and-stick*, *spacefill* (every atom as a full-size sphere), *surface*. |

**Table S0e. Terms of the corpus.**

| Term | Meaning in this paper |
|:---------|:------------------------------|
| Author numbering | The chain identifiers and residue numbers chosen by the depositors (in the structure file: `auth_asym_id`, `auth_seq_id`). This is what papers and most viewers show. A number can carry an *insertion code*: a letter appended to it (52A) where the depositors placed an extra residue between two numbers. |
| Label numbering | The chain identifiers and residue numbers assigned by the archive (`label_asym_id`, `label_seq_id`). Residues are counted 1, 2, 3 … along the full sequence of the molecule that was studied, including residues that are not seen in the coordinates, so the count has no gaps and no insertion codes. |
| UniProt numbering | The position of a residue in the UniProt canonical sequence, counted from its first residue and so including any signal peptide. The variant names we use are in this numbering unless the request says otherwise (Section S10.3). |
| Offset | For one residue, its UniProt number minus its author number ({{ex.uniprot_position}} − {{ex.auth_number}} = {{ex.offset}} in the running example). It can differ from residue to residue within a chain. A residue *has an offset* when the two numbers differ. In every clinical task with an offset the UniProt number is the larger one. |
| Copying the number | Using the number printed in a variant name as the author residue number, without converting it. Copying is *right* in a task if the answer written in this way is exactly right, and *wrong* otherwise. The property is defined on author numbering and is used to group results of the scene track only (Section S10.3). |
| Request, task, answer | The *request* is the plain-language instruction given to the model. A *task* is a request on one track, with its reference answer and, where it has one, its target; a request that is posed on both tracks is two tasks. An *answer* is what the model returns for one task. Each task is answered {{plan.samples}} times in the main condition. |
| Target | The atoms that the request is about. Most tasks store it. For a first request that only changes a viewer setting or hides something, the target is everything the reference changes. {{corpus.n_without_target_followup}} follow-up tasks have none, and means of the target score leave them out (Section 4.2). |
| Scene | An answer in MolViewSpec: a description of what to load and how to draw it. A scene groups the atoms it selects into *components*; each component is a named set of atoms that is then drawn in one or more ways. Nothing is on screen unless the scene says so. |
| Call list | An answer as an ordered list of calls to the PDBe Mol\* viewer, written in JSON (Section 3.4). |
| Default view | What the call-list viewer draws as soon as a structure is loaded, before any further call: the whole structure, with the polymer as a cartoon. A scene has no default view; its screen starts empty. |
| Track, format | A *track* is one of the two halves of the benchmark. *Scene track*: answers are MolViewSpec scenes. *Call-list track*: answers are call lists. *Format* means the answer language itself (MolViewSpec, or PDBe Mol\* calls). |
| Pair, side | A *pair* is one request posed on both tracks, with the same target atoms. A *side* is one of the two tasks of a pair. Both words are used for nothing else in this paper. |

**Table S0f. Terms of grading and of the run.** Section numbers without the letter S are
those of the paper.

| Term | Meaning in this paper |
|:---------|:------------------------------|
| Style | One representation with one colour and one opacity, for example "grey cartoon, opaque". |
| Drawn state | For every atom of the structure, the set of its styles, plus a few facts about the whole scene (labels, distance lines, the atoms the camera is centred on, viewer settings such as the background colour). On the call-list track: the changes from the default view. |
| Fact | One unit of the drawn state: all atoms that carry the same set of styles form one fact; each label, each distance line and each viewer setting that differs from the default is one fact. Atoms that are not drawn belong to no fact. |
| F1 | How much of the drawn state is right, from 0 to 1, with partial credit. For each fact of the reference, take the fraction of it that the answer also draws; *recall* is the mean of these fractions. *Precision* is the same in the other direction, over the facts of the answer. F1 is the harmonic mean of the two. |
| Task success | For one answer, yes or no: the drawn state is exactly right, with nothing missing and nothing extra. The *task success rate* of a model is the share of its answers that succeed. |
| All-{{plan.samples}} rate, majority | *All-{{plan.samples}} rate*: the share of tasks on which all {{plan.samples}} answers succeed. *Majority*: at least 2 of the {{plan.samples}} answers are right; used only in the comparison of pairs. |
| Target score | From 0 to 1: how exactly the answer marks out the target atoms. It is 1 (*target-right*) when three things hold: the target atoms carry the requested style; no other atom carries that style; and no second representation is drawn on target atoms alone. Any other drawing, such as a cartoon of the protein, is ignored. |
| Primary score | The score on which a table or a comparison is read first. *Within a track* (Tables 6 to 8, 11 and 12 of the paper): the task success rate, strict. *Between the two formats* (Table 9a of the paper) *and for copying against mapping* (Table 10 of the paper): the target score, because task success is not the same test on the two tracks and also falls when an answer adds unrequested context. The comparison of pairs on the target score is the *primary comparison* (Table 9a of the paper), and the one on task success the secondary (Table 9b). F1 is reported for partial credit and is never primary. |
| Unrequested context | Drawing that the request did not ask for, such as a cartoon of the protein behind a requested residue. |
| Valid, invalid | An answer is *valid* if it obeys the answer format and the viewer can show it: on the scene track, a scene that Mol\* accepts and whose structure file it can load; on the call-list track, a JSON list in which every call and every field is documented. Otherwise it is *invalid*, in one of two ways. An *unshowable* answer cannot be shown at all and scores 0. A *schema-breaking* call list contains parts that the viewer ignores; it is graded as the viewer would treat it but is not counted as valid (Section 4.4). |
| Call schema | The list of calls that the format guide documents, with the type of each field. A call list *fits* it if every call is on the list and every field has the documented type. |
| Strict, valid-only, repaired | Three ways to average a score (Section 4.4). *Strict* (the default): every answer counts. *Valid-only*: the mean over valid answers. *Repaired*: strict, after unparseable answers have been passed through an offline JSON repair. |
| Control, control set | A *control* is a reference and one answer whose verdict is known from how the answer was made; the *control set* is all {{controls.n:,}} of them (Section 4.5). |
| Format guide | The frozen text in the system prompt that documents the answer format (Section 5.2). |
| Grounding pack | The result of an offline lookup for one task, appended to the request in one prompting condition (Section 5.2). |
| Core models, optional models | The {{plan.n_core_models}} models that are always run, and up to {{plan.n_optional_models}} larger ones (Section 5.1). |
| Keyword script, literal script | Two scripts that use no model. The keyword script maps words of the request to fixed answers by rule. The literal script writes what the request spells out and uses every number as written. They mark the scores that need no skill and no lookup (Section 5.1). |
