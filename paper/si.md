<!-- Built by paper/build.py from paper/si/ and paper/generated/*.json (run numbers: October 2026 panel, PRELIMINARY). Do not edit: edit the sources. -->

# Supporting Information

**MolBench: Grading Language Models on What a Molecular Viewer Would Show**

This file accompanies the paper. Every table in it is written by script from the task files,
the frozen data or archived model answers. Terms are used as defined in the paper (its Box 1 and Section 4) and in Tables S0d to S0f:
*scene track* (answers are MolViewSpec scenes), *call-list track* (answers are ordered calls to
the PDBe Mol\* viewer), *drawn state*, *style*, *fact*, *F1*, *task success*, *target score*, *strict*
and *valid-only*. *Model* always means a language model. The repository and the prompts
printed in Section S7 use a few other names for the same things (a *draw* for a style, a
*tier* for a category); Table S0c lists them all. Task identifiers are those of the task
files.

Contents: S0, glossary and background terms · S1, the running example in full · S2,
all task templates · S3, the structure panel and the variant list · S4, grading rules and
known limits · S5, the control set by kind · S6, the run manifest, models and prices · S7,
the system prompts · S8, further tables of the pilot run, and the trial of the rating study ·
S9, further tables of the final run (pending) ·
S10 to S15, detail that the paper gives in one sentence each: the corpus (S10), grading
(S11), the experimental setup (S12), the pilot findings and the errors of the first version
(S13), limitations in full (S14), related work and licences (S15).

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
| Structure, entry | A set of atom coordinates. An *entry* is one deposition in the Protein Data Bank (PDB), with a four-character identifier such as 2NWD. A *predicted structure* is one computed from the sequence; ours come from the AlphaFold Protein Structure Database. |
| Coordinate set (PDB "model") | One complete set of atom positions in an entry. An entry solved by nuclear magnetic resonance usually holds several; the PDB calls each a *model* and numbers them (`pdbx_PDB_model_num`). We use the first, and we say *coordinate set* because *model* in this paper means a language model. |
| Assembly | The form in which the molecule is thought to work, for example two identical chains. An entry can deposit one copy and describe how the others are generated from it by symmetry. |
| mmCIF | The file format of the PDB archive: tables of named columns, one row per atom in the table of atoms. |
| Ligand, het group | A *ligand* is a small molecule bound to the protein. *Het group* is the older file term for any molecule in an entry that is not part of a polymer chain (a ligand, an ion, a water); each kind has an identifier of up to three characters, such as HEM for haem. |
| Helix, strand | The two common local shapes of a protein chain. An entry records where each helix and each strand begins and ends. |
| Disulfide bond | A link between the sulfur atoms of two cysteine residues. |
| Representation | A way of drawing atoms: *cartoon* (a ribbon that traces the chain), *ball-and-stick*, *spacefill* (every atom as a full-size sphere), *surface*. |
| Selection | The expression in an answer that picks atoms, for example "chain X, residue 64". |
| Alternate positions | The same atom recorded at two or more positions, where the experiment saw a residue in more than one pose (the file calls these alternate conformers). |

**Table S0b. Further terms of the corpus**, each defined in the section of the paper that is
named with it.

| Term | Meaning in the paper |
|:---------|:------------------------------|
| SIFTS | Structure Integration with Function, Taxonomy and Sequences: the public residue-by-residue mapping between PDB entries and UniProt sequences (Section 3.1). |
| Structure panel | The fixed set of 79 structures. Tasks are built on 78 of them; one, 1HSG, is reserved for the worked example of both system prompts (Section 3.1). |
| Category | One of eight kinds of task. The categories are not steps on one scale of difficulty (Section 3.3). |
| Lookup categories | Name resolution and clinical variant. In these the answer needs one piece of information that a person would look up in a database: an entry identifier, or a residue number. The model cannot look it up and must recall it (Section 3.3). |
| Template | A fixed kind of request within a category; a generator script fills in the structure, the residues, the colours and the wording (Section 3.3). |
| Accepted answer | One of several drawn states that a task lists as right. An answer is graded against each, and the best result counts (Sections 3.3 and 4.2). |
| Set-aside split | The tasks on 15 structures that were set aside before generation and that the first version of the benchmark never used, in any of its releases. The tasks are public; the split is not a hidden test set (Section 3.6). |
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
| UniProt, canonical sequence | UniProt is the reference database of protein sequences. Each protein has an accession, such as P61626, and one sequence that UniProt picks as its reference, the *canonical sequence*. |
| ClinVar | A public archive of human genetic variants. Submitters, mostly clinical laboratories, send their classification of a variant for a condition, on a scale from benign through uncertain significance to pathogenic. For each *variation record* (accession beginning with VCV; usually one change at the level of DNA) ClinVar publishes an aggregate *germline* classification, such as "Pathogenic", and a *review status*. Germline variants are present in every cell of a person, inherited or newly arisen, as opposed to somatic variants that arise in a tumour. The review status says how far the classification has been reviewed (stated criteria, several submitters in agreement, an expert panel); it is not a measure of the strength of the evidence. Different DNA changes can give the same amino-acid change, so one amino-acid change can have more than one record. We write ClinVar's terms in lower case. |
| Transcript | A reference sequence of one messenger RNA of a gene, with an accession and a version number (NM_000239.3). ClinVar states each change on a transcript, in the form c.244T>C: nucleotide 244 of the coding sequence, counted from the A of the start codon ATG, changes from T to C. A gene can have several transcripts, and they can number the protein differently. |
| Missense variant; p.W82R | A change of one amino acid into another. p.W82R: the tryptophan (W) at position 82 becomes an arginine (R). The same in three-letter form is p.Trp82Arg. The prefix "p." marks a description of a change in the protein, as opposed to "c." for the coding DNA; it does not say which sequence the position is counted on. In this paper it is the UniProt canonical sequence, here P61626. HGVS, the nomenclature of the Human Genome Variation Society for naming variants, does not accept a UniProt accession as a reference sequence (Section S10.3). |
| Signal peptide, mature protein, traditional name | The *mature protein* is what is left after the cell has removed the leading part of a newly made protein. That part can be the first residue alone, the *initiator methionine* (haemoglobin beta); a *signal peptide* (lysozyme: 18 residues); or a signal peptide and a further segment, a *propeptide* (coagulation factor IX: 46 residues). Older literature often numbers residues from the first residue of the mature protein; we call a variant name of this kind a *traditional name* (the genetics literature also says legacy name) and its numbering *mature-protein numbering*. A traditional name carries no "p.", as in W64R. |
| Mol\*, MolViewSpec | Mol\* is an open-source molecular viewer that runs in a web browser. MolViewSpec is a format, written in JSON (JavaScript Object Notation), that describes what Mol\* should load and draw. PDBe Mol\* is the build of Mol\* maintained by the Protein Data Bank in Europe (PDBe). |
| Polymer, ligand | The *polymer* is the protein, DNA or RNA chains of a structure. A *ligand* is a small molecule bound to them. |
| Representation | A way of drawing atoms: *cartoon* (a ribbon that traces the whole polymer chain, the usual background of a picture), *ball-and-stick*, *spacefill* (every atom as a full-size sphere), *surface*. |

**Table S0e. Terms of the corpus.**

| Term | Meaning in this paper |
|:---------|:------------------------------|
| Author numbering | The chain identifiers and residue numbers chosen by the depositors (in the structure file: `auth_asym_id`, `auth_seq_id`). This is what papers and most viewers show. A number can carry an *insertion code*: a letter appended to it (52A) where the depositors placed an extra residue between two numbers. |
| Label numbering | The chain identifiers and residue numbers assigned by the archive (`label_asym_id`, `label_seq_id`). Residues are counted 1, 2, 3 … along the full sequence of the molecule that was studied, including residues that are not seen in the coordinates, so the count has no gaps and no insertion codes. |
| UniProt numbering | The position of a residue in the UniProt canonical sequence, counted from its first residue and so including any signal peptide. The variant names we use are in this numbering unless the request says otherwise (Section S10.3). |
| Offset | For one residue, its UniProt number minus its author number (82 − 64 = 18 in the running example). It can differ from residue to residue within a chain. A residue *has an offset* when the two numbers differ. In every clinical task with an offset the UniProt number is the larger one. |
| Copying the number | Using the number printed in a variant name as the author residue number, without converting it. Copying is *right* in a task if the answer written in this way is exactly right, and *wrong* otherwise. The property is defined on author numbering and is used to group results of the scene track only (Section S10.3). |
| Request, task, answer | The *request* is the plain-language instruction given to the model. A *task* is a request on one track, with its reference answer and, where it has one, its target; a request that is posed on both tracks is two tasks. An *answer* is what the model returns for one task. Each task is answered 3 times in the main condition. |
| Target | The atoms that the request is about. Most tasks store it. For a first request that only changes a viewer setting or hides something, the target is everything the reference changes. 31 follow-up tasks have none, and means of the target score leave them out (Section 4.2). |
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
| All-3 rate, majority | *All-3 rate*: the share of tasks on which all 3 answers succeed. *Majority*: at least 2 of the 3 answers are right; used only in the comparison of pairs. |
| Target score | From 0 to 1: how exactly the answer marks out the target atoms. It is 1 (*target-right*) when three things hold: the target atoms carry the requested style; no other atom carries that style; and no second representation is drawn on target atoms alone. Any other drawing, such as a cartoon of the protein, is ignored. |
| Primary score | The score on which a table or a comparison is read first. *Within a track* (Tables 6 to 8, 11 and 12 of the paper): the task success rate, strict. *Between the two formats* (Table 9a of the paper) *and for copying against mapping* (Table 10 of the paper): the target score, because task success is not the same test on the two tracks and also falls when an answer adds unrequested context. The comparison of pairs on the target score is the *primary comparison* (Table 9a of the paper), and the one on task success the secondary (Table 9b). F1 is reported for partial credit and is never primary. |
| Unrequested context | Drawing that the request did not ask for, such as a cartoon of the protein behind a requested residue. |
| Valid, invalid | An answer is *valid* if it obeys the answer format and the viewer can show it: on the scene track, a scene that Mol\* accepts and whose structure file it can load; on the call-list track, a JSON list in which every call and every field is documented. Otherwise it is *invalid*, in one of two ways. An *unshowable* answer cannot be shown at all and scores 0. A *schema-breaking* call list contains parts that the viewer ignores; it is graded as the viewer would treat it but is not counted as valid (Section 4.4). |
| Call schema | The list of calls that the format guide documents, with the type of each field. A call list *fits* it if every call is on the list and every field has the documented type. |
| Strict, valid-only, repaired | Three ways to average a score (Section 4.4). *Strict* (the default): every answer counts. *Valid-only*: the mean over valid answers. *Repaired*: strict, after unparseable answers have been passed through an offline JSON repair. |
| Control, control set | A *control* is a reference and one answer whose verdict is known from how the answer was made; the *control set* is all 2,175 of them (Section 4.5). |
| Format guide | The frozen text in the system prompt that documents the answer format (Section 5.2). |
| Grounding pack | The result of an offline lookup for one task, appended to the request in one prompting condition (Section 5.2). |
| Core models, optional models | The 16 models that are always run, and up to 5 larger ones (Section 5.1). |
| Keyword script, literal script | Two scripts that use no model. The keyword script maps words of the request to fixed answers by rule. The literal script writes what the request spells out and uses every number as written. They mark the scores that need no skill and no lookup (Section 5.1). |

## S1. The running example in full

The request, the two reference answers, the further accepted answers on the call-list track,
the stored target and the grounding pack, exactly as they are in the task files
`clin-pair-target-lyz-2nwd-w82r-mvs` (scene track) and `clin-pair-target-lyz-2nwd-w82r-api` (call-list track). The variant is
*LYZ* p.W82R (p.Trp82Arg; UniProt P61626). UniProt names the disease
as "Familial visceral amyloidosis, Ostertag type (AMYLD2)". Through UniProt's cross-references we found 2
ClinVar records of this protein change, one for each of the two single-nucleotide changes
that turn the codon of this tryptophan into a codon of arginine: VCV000014376, NM_000239.3(LYZ):c.244T>C (p.Trp82Arg); VCV000014378, NM_000239.3(LYZ):c.244T>A (p.Trp82Arg). Both carry the aggregate
classification "pathogenic" and the review status
"criteria provided, single submitter"; ClinVar's own field for the condition reads
"not provided" on both. The entry 2NWD is human lysozyme at
1.04 Å resolution; the target residue has 24 atom records
(14 non-hydrogen atoms and 10 hydrogens, which
this entry contains).

On the call-list track the viewer starts with the protein drawn as a cartoon. The reference
sets `"color": null` on the residue, which leaves that cartoon as it was. Without that field
the viewer also recolours the residue's own segment of the cartoon, in its selection colour.
The request says nothing about the cartoon, so an answer that recolours the segment, in the
selection colour or in yellow as the residue is, is accepted as well.

**Request (both tracks).** PDB entry 2NWD: the LYZ (Lysozyme C, UniProt P61626) variant p.W82R is classified as pathogenic in ClinVar. Show the residue it replaces as yellow spacefill spheres.

**Scene track, task `clin-pair-target-lyz-2nwd-w82r-mvs`: reference answer.**

```json
{
 "root": {
  "kind": "root",
  "children": [
   {
    "kind": "download",
    "params": {
     "url": "https://files.rcsb.org/download/2nwd.cif"
    },
    "children": [
     {
      "kind": "parse",
      "params": {
       "format": "mmcif"
      },
      "children": [
       {
        "kind": "structure",
        "params": {
         "type": "model"
        },
        "children": [
         {
          "kind": "component",
          "params": {
           "selector": {
            "auth_asym_id": "X",
            "auth_seq_id": 64
           }
          },
          "children": [
           {
            "kind": "representation",
            "params": {
             "type": "spacefill"
            },
            "children": [
             {
              "kind": "color",
              "params": {
               "color": "yellow"
              }
             }
            ]
           }
          ]
         }
        ]
       }
      ]
     }
    ]
   }
  ]
 }
}
```

**Call-list track, task `clin-pair-target-lyz-2nwd-w82r-api`: reference answer.**

```json
[
 {
  "action": "load",
  "molecule_id": "2nwd"
 },
 {
  "action": "color",
  "data": [
   {
    "uniprot_accession": "P61626",
    "uniprot_residue_number": 82,
    "color": null,
    "representation": "spacefill",
    "representationColor": "yellow"
   }
  ]
 }
]
```

**Call-list track: accepted answers** (2; the residue's own segment of the cartoon is recoloured as well, in the residue's colour or in the viewer's selection colour).

```json
[
 {
  "action": "load",
  "molecule_id": "2nwd"
 },
 {
  "action": "color",
  "data": [
   {
    "uniprot_accession": "P61626",
    "uniprot_residue_number": 82,
    "color": "yellow",
    "representation": "spacefill",
    "representationColor": "yellow"
   }
  ]
 }
]
```

```json
[
 {
  "action": "load",
  "molecule_id": "2nwd"
 },
 {
  "action": "color",
  "data": [
   {
    "uniprot_accession": "P61626",
    "uniprot_residue_number": 82,
    "representation": "spacefill",
    "representationColor": "yellow"
   }
  ]
 }
]
```

**Target** (the atoms the request is about, stored in label numbering on both tasks).

```json
[
 {
  "selector": {
   "label_asym_id": "A",
   "label_seq_id": 64
  },
  "representation": "spacefill",
  "color": "yellow"
 }
]
```

**Grounding pack** (appended to the request only in the grounding-pack condition).

```text
PDB 2NWD: Structure of chemically synthesized human lysozyme at 1 Angstrom resolution
Method: X-RAY DIFFRACTION, 1.04 Å
Polymer chains (author chain [label chain]; observed residues as author numbering = label numbering):
  X [A]: entity 1 (Lysozyme C), protein, 130 of 130 residues observed: auth 1-130 = label 1-130
UniProt mapping (SIFTS; observed residues as UniProt numbering = author numbering):
  X [A]: P61626 (LYSC_HUMAN): UniProt 19-148 = auth 1-130

From the request:
  LYZ: UniProt P61626 (LYSC_HUMAN, Lysozyme C)
  p.W82R: UniProt position 82 (Trp in UniProt) -> in 2NWD: auth X 64 TRP (label A 64)
```

**Table S1. Scores of the answers discussed in Sections 4.2 and 4.3 of the paper** (the same as Table 3 of the paper). *F1*: how much of
the drawn state is right (0 to 1). *Task success*: the drawn state is exactly right. *Target
score* (0 to 1): how exactly the answer marks out the requested atoms. It is 1 (*target-right*) when three things hold: the target atoms carry the requested style; no other atom carries that style; and no second representation is drawn on target atoms alone. Any other drawing, such as a cartoon of the protein, is ignored. Rows S1 to S10 are scenes, rows C1 to C7 call lists. *Spill*, *extra on the target* and *context* are the three rules for extra
drawing of Section S4.3.

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

## S2. Task templates

A template fixes what is asked; a seeded generator fills in the structure, the residues, the
colours and the wording. The corpus has 129 templates. No template supplies more than
12% of a category's tasks, except in name resolution (there
are only five ways to name a protein) and in the small call-list category of requests with
several right answers.

**Table S2. Every template, with its number of tasks on each track and one example request**
(shortened where long). A dash means that the template has no task on that track. Template
names are the identifiers used in the task files.

| Category | Template | Scene tasks | Call-list tasks | Example request |
|:----|:-----|--:|--:|:----------------|
| Translation | `api-assembly` | – | 6 | Load oxyhaemoglobin (1HHO) as its biological assembly (the tetramer, assembly 1) and show it as a molecular surface. |
| Translation | `api-atoms` | – | 5 | Open 1AAY in the ball-and-stick style; atoms CB and OD1 of Asp166 of chain A should be cyan. |
| Translation | `api-chain-colour` | – | 10 | Load insulin (4INS) as a cartoon. Colour the two A chains (author chains A and C) blue and the two B chains (author chains B and D) yellow, and show the zinc ions (ZN)… |
| Translation | `api-entity` | – | 5 | In 1AOI, colour by molecule: entity 3 (protein) cyan and entity 4 (protein) steel blue. Leave the other entities alone. |
| Translation | `api-hide` | – | 11 | Load the myoglobin structure 1A6M and hide all the water molecules. |
| Translation | `api-inscode` | – | 5 | Load 1IGT and colour Asn52A of chain D purple: the residue with insertion code A, not the other residue numbered 52. In the mmCIF label numbering it is residue 53 of l… |
| Translation | `api-keep-sticks` | – | 3 | Open 1D5R. Step one: Asp268 as ball-and-stick. Step two, on top of step one: Thr26 as spacefill. Element colours for both, and no other colour changes. |
| Translation | `api-label-chain` | – | 5 | In 1ATP, colour label chain B hot pink: B is the mmCIF label chain id, not the author chain id. |
| Translation | `api-layered-colour` | – | 7 | Open 1A3K; residues 197 to 204 in plum, but Val202 in hot pink. |
| Translation | `api-ligand` | – | 8 | Load streptavidin (1STP), hide the waters, and centre the view on the bound biotin (BTN). |
| Translation | `api-ligand-sticks` | – | 3 | Open haemoglobin (1HHO) and show the heme groups (HEM) in ball-and-stick coloured orange, with the rest as cartoon. |
| Translation | `api-range-colour` | – | 9 | Load ubiquitin (1UBQ) and colour the C-terminal tail, residues 71 to 76, red and the rest of the structure white. |
| Translation | `api-residue-colour` | – | 9 | Load 1AAY and colour Ser147, Ala164 and Glu177 of chain A khaki. |
| Translation | `api-residue-sticks` | – | 7 | Load hen egg-white lysozyme (1LYZ) as a cartoon, colour the two catalytic residues Glu35 and Asp52 red, and also show them as a red molecular surface. |
| Translation | `api-sticks-plain` | – | 3 | Open 1D5R and draw His61 as ball-and-stick on top of the default view; keep every colour at its default. |
| Translation | `api-style-colour` | – | 5 | Show 1CRN as putty and colour residues 14 to 20 purple. |
| Translation | `api-uniprot-range` | – | 6 | Load 1IGT and colour residues 108 to 121 of UniProt P01863 in both chains that have them orange. |
| Translation | `api-uniprot-residue` | – | 9 | Load 1AKI and colour His33 and Asn62 purple. The numbers are in UniProt numbering (P00698). |
| Translation | `tr-cartoon` | 4 | 4 | Open PDB entry 1C3W; draw the whole protein as a cartoon, coloured yellow. |
| Translation | `tr-chain-colour` | 4 | 4 | Load 1K4C as a grey cartoon and colour chain A blue. |
| Translation | `tr-chain-only` | 4 | 4 | Load 1AKE and show only chain A, as a teal cartoon. |
| Translation | `tr-chains-named` | 4 | 4 | Load 4INS as a cartoon and colour chain A magenta, chain B cyan, chain C plum and chain D red. |
| Translation | `tr-colour-by-chain` | 5 | – | Load 1AOI and show it as a cartoon coloured by chain. |
| Translation | `tr-glycans` | 4 | 4 | 1A3K: grey cartoon for the protein, hot pink ball-and-stick for the bound sugar. |
| Translation | `tr-het-code` | 4 | 4 | Show 1CBS as a grey cartoon with the REA residue in teal ball-and-stick. |
| Translation | `tr-ions` | 4 | 4 | Show 2P4E as a grey cartoon with the metal ions drawn as hot pink spheres. |
| Translation | `tr-ligands` | 4 | 4 | 1HVR: grey cartoon for the protein, magenta ball-and-stick for the ligand. |
| Translation | `tr-nucleic` | 5 | 5 | 1AAY, cartoon: DNA khaki, protein salmon. |
| Translation | `tr-range-labels` | 4 | – | Load 1A6M as a grey cartoon, then colour residues 5-12 of chain A yellow with the text label "patch B" and colour residues 68-79 of chain A red with the text label "si… |
| Translation | `tr-range-rows` | 4 | 4 | Load 1ATP as a grey cartoon and colour these segments: chain E 16-30 yellow; chain E 58-69 salmon. |
| Translation | `tr-range-sticks` | 5 | 5 | Load 1CRN as a grey cartoon and show residues 14-23 as brown ball-and-stick. |
| Translation | `tr-rep-word` | 4 | 2 | Load 1MBN and show the protein as brown space-filling spheres. |
| Translation | `tr-residue-focus` | 4 | 4 | 1EMA: grey cartoon, residue 196 as orange ball-and-stick, camera focused on the residue. |
| Translation | `tr-strands` | 3 | 3 | Load 1AAY and show the two DNA strands as cartoons: chain B in teal and chain C in blue. Nothing else. |
| Translation | `tr-surface` | 4 | 4 | Load 1AKI and show the protein as a steel blue molecular surface. |
| Translation | `tr-water` | 3 | 3 | Show 1IRO as a blue cartoon together with its waters as teal spheres. |
| Structure-grounded | `gr-all-but-chain` | 3 | 3 | 1LMB as an orange cartoon without chain 2: hide that chain and keep all the others. |
| Structure-grounded | `gr-attachment` | 4 | 4 | Show 1C3W as a grey cartoon with the retinal in steel blue ball-and-stick and the lysine that holds it covalently in lime green ball-and-stick. |
| Structure-grounded | `gr-catalytic` | 6 | 6 | 1AKI: grey cartoon, with the two catalytic residues drawn as green ball-and-stick. |
| Structure-grounded | `gr-disulfides` | 6 | 6 | 1CRN: grey cartoon, with every disulfide-bonded cysteine drawn in plum ball-and-stick. |
| Structure-grounded | `gr-entity` | 6 | 6 | Show 1AOI as a cartoon coloured by molecule: the two H3 histones orange, the two H4 histones brown, the two H2A histones red, the two H2B histones khaki and everything… |
| Structure-grounded | `gr-glyco-sites` | 5 | 5 | Show 1IGT as a grey cartoon and mark the glycosylation sites: the asparagines that carry a sugar, in brown ball-and-stick. Do not draw the sugars. |
| Structure-grounded | `gr-heme` | 4 | 4 | Load 1MBN; show the protein as a grey cartoon and the heme group as teal spheres. |
| Structure-grounded | `gr-heme-axial` | 4 | 4 | Load 1A6M; show the protein as a grey cartoon, the heme as teal ball-and-stick, and the protein residue bonded to the heme iron as hot pink ball-and-stick. |
| Structure-grounded | `gr-ligand` | 6 | 6 | In 1AKE, draw the protein as a grey cartoon and pick out the AP5A in lime green ball-and-stick. |
| Structure-grounded | `gr-longest-helix` | 4 | 4 | Load 1D5R as a grey cartoon and colour its longest helix lime green, going by the helix records of the entry. |
| Structure-grounded | `gr-metal-site` | 6 | 6 | 1IRO: grey cartoon; iron ion as a khaki sphere; every residue of the protein that coordinates the iron ion, as green ball-and-stick. |
| Structure-grounded | `gr-modres` | 5 | 5 | Show 1ATP as a grey cartoon and highlight the phosphorylated residues in lime green ball-and-stick. |
| Structure-grounded | `gr-secstruct` | 4 | 4 | Show 1A3K as a grey cartoon, then colour the helices blue and the beta strands lime green, following the helix and sheet records of the entry. |
| Name resolution | `res-complex` | 3 | – | Find a PDB entry of bovine trypsin in complex with bovine pancreatic trypsin inhibitor (BPTI) and show it as a plum cartoon. |
| Name resolution | `res-dna` | 3 | – | I want to see how the cI repressor of bacteriophage lambda sits on DNA. Any PDB structure of the complex will do: protein as a brown cartoon, DNA as a teal cartoon. |
| Name resolution | `res-gene` | 11 | – | I want to see a structure of human SOD1; a green cartoon will do. |
| Name resolution | `res-ligand` | 10 | – | Find a PDB entry of human phosphodiesterase 5A (PDE5A) in complex with sildenafil; draw the protein as a lime green cartoon and the sildenafil in purple ball-and-stick. |
| Name resolution | `res-name` | 12 | – | Find a PDB entry of horse heart cytochrome c and show it as a yellow cartoon. |
| Clinical variant | `clin-chain` | 8 | 8 | PDB entry 8EPH: the F9 (Coagulation factor IX, UniProt P00740) variant p.Gly412Glu is classified as pathogenic in ClinVar. Show the residue it replaces as magenta ball… |
| Clinical variant | `clin-hgvs-context` | 6 | 6 | PDB entry 8CE0: the APOE (Apolipoprotein E) variant p.Arg43Cys is classified as pathogenic/likely pathogenic in ClinVar. Show the whole structure as a white cartoon, w… |
| Clinical variant | `clin-hgvs-target` | 5 | 5 | In PDB entry 5CJ6, show the residue replaced by the likely pathogenic AR (Androgen receptor) variant p.Leu702Phe (ClinVar) as purple ball-and-stick. |
| Clinical variant | `clin-legacy-context` | 6 | 6 | In PDB entry 1HK0, show the whole structure as a gray cartoon and the residue replaced by the likely pathogenic CRYGD (Gamma-crystallin D, UniProt P07320) variant L44P… |
| Clinical variant | `clin-legacy-target` | 7 | 7 | In PDB entry 8CE0, show the residue replaced by the likely pathogenic APOE (Apolipoprotein E) variant R136L (ClinVar) as green ball-and-stick. The name R136L is in mat… |
| Clinical variant | `clin-multi-context` | 4 | 4 | In PDB entry 5CJ6, show the whole structure as a white cartoon and the residues replaced by the AR (Androgen receptor) variants p.P724S and p.M781I (each pathogenic or… |
| Clinical variant | `clin-multi-target` | 4 | 4 | Using PDB entry 6M7H, show as green spacefill spheres the wild-type residues at the positions of the CALM1 (Calmodulin-1) missense variants p.Thr30Pro, p.Glu105Lys and… |
| Clinical variant | `clin-pair-context` | 8 | 8 | PDB entry 1HK0: the CRYGD (Gamma-crystallin D, UniProt P07320) variant p.Arg37Pro is classified as likely pathogenic in ClinVar. Show the whole structure as a khaki ca… |
| Clinical variant | `clin-pair-target` | 10 | 10 | Using PDB entry 6M7H, show as cyan spacefill spheres the wild-type residue at the position of the CALM1 (Calmodulin-1, UniProt P0DP23) missense variant p.Phe142Leu (pa… |
| Clinical variant | `clin-short-context` | 5 | 5 | In PDB entry 5EDM, show the whole structure as a white cartoon and the residue replaced by the pathogenic/likely pathogenic F2 (Prothrombin) variant p.R461W (ClinVar)… |
| Clinical variant | `clin-short-target` | 9 | 9 | In PDB entry 5UAK, show the residue replaced by the pathogenic CFTR (Cystic fibrosis transmembrane conductance regulator) variant p.G551D (ClinVar) as magenta ball-and… |
| Clinical variant | `clin-sse-helix` | 5 | 5 | PDB entry 6M7H: the CALM1 (Calmodulin-1, UniProt P0DP23) variant p.E141V is classified as pathogenic in ClinVar. Show the helix (as annotated in the entry) that contai… |
| Clinical variant | `clin-sse-strand` | 5 | 5 | PDB entry 1HK0: the CRYGD (Gamma-crystallin D, UniProt P07320) variant p.Arg59His is classified as pathogenic in ClinVar. Show the beta strand (as annotated in the ent… |
| Interactions | `in-ca-distance` | 5 | – | Show 1AKE as a yellow cartoon. Add a distance measurement (dashed line with the value as label) from the CA atom of Ser183 to the CA atom of Lys200. Both residues are… |
| Interactions | `in-computed` | 5 | – | 1A6M: grey cartoon; heme as red ball-and-stick with its computed non-covalent interactions shown; camera on the heme. |
| Interactions | `in-disulfide` | 5 | – | In 1F88 (grey cartoon), measure the S-S bond of the disulfide between Cys110 and Cys187: the two cysteines in green ball-and-stick, a labelled dashed line between thei… |
| Interactions | `in-hbond` | 5 | – | 1A3K: grey cartoon; Asn174 and Arg224 as magenta ball-and-stick; measure the hydrogen bond between OD1 of Asn174 and NH1 of Arg224 with a labelled dashed line; focus t… |
| Interactions | `in-ligand-contact` | 5 | – | 1ATP: grey cartoon; ATP as teal ball-and-stick; Phe54 as cyan ball-and-stick; measure the contact between ATP atom O2B and N of Phe54 with a labelled dashed line; focu… |
| Interactions | `in-metal-contact` | 5 | – | 1HRC: grey cartoon; heme as plum ball-and-stick; His18 and Met80 as salmon ball-and-stick; measure the distance from the heme iron to NE2 of His18 and SD of Met80 with… |
| Interactions | `in-salt-bridge` | 5 | – | Load 1EMA as a grey cartoon. Show Lys3 and Glu90 as cyan ball-and-stick, draw the salt bridge between the NZ atom of Lys3 and the OE1 atom of Glu90 as a dashed line la… |
| Interactions | `in-transparent` | 5 | – | Show 1CTQ with a semi-transparent brown protein surface (opacity 0.5) so that the GppNHp, drawn in steel blue ball-and-stick, can be seen through it. |
| Follow-up turn | `fu-add-chain` | 2 | – | Also show chain 4 as a blue cartoon. |
| Follow-up turn | `fu-add-label` | 2 | – | Add a label reading "BTN" to the biotin (BTN). |
| Follow-up turn | `fu-add-ligand` | 2 | – | Now bring in the ligand HEM in plum ball-and-stick. |
| Follow-up turn | `fu-add-residue` | 4 | 4 | Now draw His122 of chain A as ball-and-stick too, in yellow; the cartoon keeps its colour. |
| Follow-up turn | `fu-also-colour-chain` | 2 | 2 | Now colour chain B as well, in brown. |
| Follow-up turn | `fu-api-clear-colours` | – | 1 | Go back to the default colours; the waters stay hidden. |
| Follow-up turn | `fu-api-show-water` | – | 2 | Bring the water molecules back. |
| Follow-up turn | `fu-api-stop-spin` | – | 1 | Stop the spinning. |
| Follow-up turn | `fu-api-style` | – | 2 | Switch the whole structure to the putty style and keep the two chain colours. |
| Follow-up turn | `fu-api-uncolour` | – | 2 | Put the retinal (RET) back to its default colours; the protein stays yellow. |
| Follow-up turn | `fu-background` | 2 | 2 | Black background, please. |
| Follow-up turn | `fu-focus-ligand` | 2 | 2 | Now focus the camera on the ligand GNP. |
| Follow-up turn | `fu-hide-water` | 2 | 2 | Get rid of the waters, please. |
| Follow-up turn | `fu-it-colour` | 2 | – | Colour it steel blue. |
| Follow-up turn | `fu-it-surface` | 1 | – | Make it a surface instead of a cartoon. |
| Follow-up turn | `fu-noop-colour` | 2 | 2 | Show the heme c (HEC) in cyan. |
| Follow-up turn | `fu-noop-hidden` | 2 | 2 | Hide the waters. |
| Follow-up turn | `fu-noop-ligand-rep` | 2 | 2 | Show the ligand HEM as ball-and-stick. |
| Follow-up turn | `fu-noop-shown` | 2 | 2 | Cartoon for the protein, please. |
| Follow-up turn | `fu-noop-spin` | 2 | – | Make the structure spin slowly, or leave the scene as it is if spinning is not possible here. |
| Follow-up turn | `fu-only-chain` | 2 | – | Only chain A, please. |
| Follow-up turn | `fu-opacity` | 2 | – | Can you make the surface of the protein 70% transparent? |
| Follow-up turn | `fu-other-chain` | 2 | 2 | Colour the other chain grey. |
| Follow-up turn | `fu-recolour-chain` | 2 | 2 | Change chain I to yellow. |
| Follow-up turn | `fu-recolour-ligand` | 3 | 3 | Could you turn the ligand XK2 blue? |
| Follow-up turn | `fu-referent-colour` | 3 | 3 | Change the teal chain to brown. |
| Follow-up turn | `fu-remove-label` | 1 | – | Take the label off. |
| Follow-up turn | `fu-remove-ligand` | 2 | – | Remove the ligand ATP from the view. |
| Follow-up turn | `fu-rep-ligand` | 2 | – | Show the ligand XK2 as spacefill instead of ball-and-stick. |
| Follow-up turn | `fu-rep-polymer` | 2 | – | Switch the protein from cartoon to surface. |
| Follow-up turn | `fu-same-colour-as` | 2 | 2 | Give the retinoic acid (REA) the same colour as the protein. |
| Follow-up turn | `fu-swap-colours` | 2 | 2 | Swap the colours of the two chains. |
| Follow-up turn | `fu-undo-grey` | 2 | 2 | Undo the magenta on the biotin (BTN): grey again, please. |
| Several right answers | `acc-chain-colours` | 3 | 3 | Load 1AAY and show it as a cartoon, with the three chains coloured green, magenta and cyan. |
| Several right answers | `acc-ligand-colours` | 3 | 3 | Show 1RX2 with the protein as a cartoon and the two ligands as ball-and-stick: one cyan, the other blue. |
| Several right answers | `acc-ligand-copy` | 3 | 3 | Open 1IEP with the protein as a cartoon and the ligand STI in purple ball-and-stick. |
| Several right answers | `acc-ligand-which` | 3 | 3 | Open 1RX2 with the protein as a cartoon and the ligand in cyan ball-and-stick. |
| Several right answers | `acc-metal-copy` | 3 | – | Show 1TUP with the protein and DNA as a cartoon and the zinc ion as a spacefill sphere, coloured magenta. |
| Several right answers | `acc-metal-which` | 2 | – | Open 1UDT with the protein as a cartoon and the metal ion in red spacefill. |
| Several right answers | `acc-representation-open` | 3 | – | Open 1MBN with the protein as a cartoon, and show the heme in blue. |
| Several right answers | `acc-residue-colour` | 3 | 3 | Show 1AOI with the protein and DNA as a cartoon. Colour Ile66 blue. |
| Several right answers | `acc-residue-copy` | 3 | – | Show 1TRN with the protein as a cartoon and Lys236 as ball-and-stick, coloured purple. |
| Viewer settings | `api-alphafold` | – | 3 | Load the AlphaFold DB model of human p53 (UniProt P04637) and colour it by the model's per-residue confidence (pLDDT). |
| Viewer settings | `api-canvas` | – | 4 | Show insulin (4INS), hide the waters and the heteroatoms, set glossy lighting, and make it slowly spin. |
| Viewer settings | `api-domain-overlay` | – | 3 | Load hen egg-white lysozyme (1AKI) as a cartoon, overlay the domain annotations, and attach a tooltip reading 'catalytic glutamate' to Glu35 on chain A. |
| Viewer settings | `api-highlight` | – | 3 | Load haemoglobin (1HHO), set the hover-highlight colour to yellow and the selection colour to cyan, and highlight the heme groups (HEM). |
| Viewer settings | `api-ligand-view` | – | 3 | I want the ligand view for the ligand XK2 of 1HVR: just that ligand with its environment, white background. |
| Viewer settings | `api-maps` | – | 2 | Load 3ERT with its electron-density maps, drawing the positive Fo-Fc difference map as a wireframe at opacity 0.7. |
| Viewer settings | `api-preset` | – | 2 | Load 1BNA showing the whole unit cell, on a black background. |
| Viewer settings | `api-superposition` | – | 3 | Open the PDBe-KB superposition view for human haemoglobin subunit alpha (UniProt P69905) on a white background. |
| Viewer settings | `api-symmetry-overlay` | – | 1 | Open 2OMF as assembly 1, the trimer, with the symmetry annotation turned on. |
| Viewer settings | `api-tooltips` | – | 3 | In 1C3W, switch off the water molecules and add hover tooltips reading 'Leu100' on Leu100 and 'Gly218' on Gly218. |
| Viewer settings | `api-undo` | – | 4 | Load 1F88 and hide the waters. Colour both copies of the retinal (RET) orange and highlight chain A; then clear the highlight again. |
| Viewer settings | `api-validation-overlay` | – | 3 | Load the A2A adenosine receptor (3EML) as a cartoon and overlay the PDBe geometry-validation colouring. |

## S3. The structure panel and the variant list

### S3.1 The structure panel

**Methods.** Of the 74 PDB entries, 68 were solved by X-ray
crystallography, 4 by cryo-electron microscopy and 2 by nuclear
magnetic resonance.

**Selection rule.** The panel is the union of four groups. Every entry must be current in the
PDB archive and have at most 15,000 atoms in its first coordinate set, so that
it renders quickly (2 larger entries are kept because earlier tasks
used them). Every feature claimed for an entry (ligand, haem, metal, disulfide, nucleic acid,
glycan, membrane protein, assembly that differs from the deposited coordinates, insertion
codes, author chain identifiers that differ from label identifiers, a UniProt numbering
offset) must be found in the file by the build script, or the build fails.

1. *Entries used by earlier tasks.*
2. *Named entries*, chosen by hand to cover folds and features that the first group lacks.
   Well-known entries were preferred, solved by X-ray crystallography at 2.5 Å or better where
   one exists. The choice is by hand; the check of each claimed feature is by script.
3. *Disease proteins.* 27 human proteins in which germline missense
   variants cause Mendelian disease are listed by UniProt accession. The list was written by hand:
   familiar examples that have experimental structures. For each, candidate entries are all PDB entries that SIFTS maps to the accession.
   The script keeps X-ray entries at 2.5 Å or better that cover at least one variant position
   (failing that, X-ray or cryo-electron microscopy entries at 3.5 Å or better), drops entries
   above the size limit or with several coordinate sets, and then chooses by, in order: most
   variant positions covered, fewest engineered mutations, fewest polymer entities, best
   resolution. Whether the author numbering differs from UniProt was not a criterion. A
   variant may also be asked on any other panel structure of the same protein.
4. *5 predicted structures* from the AlphaFold Protein Structure Database,
   which use UniProt numbering by construction: of p53, gamma-crystallin D, calmodulin-1, lysozyme and haemoglobin beta. The predicted
   structure of p53 was used by earlier tasks. Each of the others is a partner to an
   experimental structure of the same protein that is numbered differently, so that the same
   variant can be asked with and without an offset.

Counts of verified features in the panel: ligand 44, metal
36, disulfide 24, assembly differs
16, author chain identifier differs from label identifier
15, glycan 10, nucleic acid
8, modified residue 8, haem
7, insertion codes 7, membrane protein
7. Structure files were retrieved on 16 November 2026; the
checksum of each file is stored with the panel.

**Atom tables and mapping tables.** The atom table of a structure lists every atom record of
the first coordinate set of its file. It keeps *alternate conformers*, the same atom recorded
at two or more positions where the experiment saw a residue in more than one pose
(29 structures have them), and hydrogen atoms, which many
files omit (13 structures have them). A selection of a residue takes
all of its atom records, as the viewer does. An author residue number is used together with
its insertion code where there is one (7 entries have them).
The mapping table holds the SIFTS correspondence between each observed residue and its
UniProt position; it is read from the copy of the entry's file that PDBe distributes with the
SIFTS mapping added, whereas the atom table is built from the archive file.

**Table S3. The panel.** *Atoms*: atoms in the first coordinate set. *Author numbering differs
from UniProt*: at least one observed residue has an author number that is not its UniProt
position (a dash: no protein chain mapped to UniProt). *Split*: set aside (one of the 15 structures of the set-aside
split; Section 3.6 of the paper), or other. *Tasks*: tasks of the
corpus on this structure, both tracks, without rephrasings.

| Entry | Title (as deposited) | Method | Deposited | Atoms | Author numbering differs from UniProt | Split | Tasks |
|:---|:------------|:----|:----|---:|:---|:---|---:|
| 1A3K | X-RAY CRYSTAL STRUCTURE OF THE HUMAN GALECTIN-3 CARBOHYDRATE RECOGNITION DOMAIN (CRD) A… | X-ray 2.10 Å | 1998-01-22 | 1253 | no | other | 8 |
| 1A6M | OXY-MYOGLOBIN, ATOMIC RESOLUTION | X-ray 1.00 Å | 1998-02-26 | 1584 | yes | other | 9 |
| 1AAY | ZIF268 ZINC FINGER-DNA COMPLEX | X-ray 1.60 Å | 1997-01-18 | 1330 | yes | other | 9 |
| 1AKE | STRUCTURE OF THE COMPLEX BETWEEN ADENYLATE KINASE FROM ESCHERICHIA COLI AND THE INHIBIT… | X-ray 2.00 Å | 1991-11-08 | 3816 | no | other | 9 |
| 1AKI | THE STRUCTURE OF THE ORTHORHOMBIC FORM OF HEN EGG-WHITE LYSOZYME AT 1.5 ANGSTROMS RESOL… | X-ray 1.50 Å | 1997-05-19 | 1079 | yes | other | 6 |
| 1AOI | COMPLEX BETWEEN NUCLEOSOME CORE PARTICLE (H3,H4,H2A,H2B) AND 146 BP LONG DNA FRAGMENT | X-ray 2.80 Å | 1997-07-03 | 12385 | yes | other | 9 |
| 1ATP | 2.2 angstrom refined crystal structure of the catalytic subunit of cAMP-dependent prote… | X-ray 2.20 Å | 1993-01-08 | 3070 | yes | other | 12 |
| 1BNA | STRUCTURE OF A B-DNA DODECAMER. CONFORMATION AND DYNAMICS | X-ray 1.90 Å | 1981-01-26 | 566 | – | other | 8 |
| 1C3W | BACTERIORHODOPSIN/LIPID COMPLEX AT 1.55 A RESOLUTION | X-ray 1.55 Å | 1999-07-28 | 2073 | yes | other | 11 |
| 1CBS | CRYSTAL STRUCTURE OF CELLULAR RETINOIC-ACID-BINDING PROTEINS I AND II IN COMPLEX WITH A… | X-ray 1.80 Å | 1994-09-28 | 1213 | yes | other | 10 |
| 1CRN | WATER STRUCTURE OF A HYDROPHOBIC PROTEIN AT ATOMIC RESOLUTION. PENTAGON RINGS OF WATER… | X-ray 1.50 Å | 1981-04-30 | 327 | no | other | 5 |
| 1CTQ | STRUCTURE OF P21RAS IN COMPLEX WITH GPPNHP AT 100 K | X-ray 1.26 Å | 1999-08-20 | 1655 | no | other | 12 |
| 1D3Z | UBIQUITIN NMR STRUCTURE | NMR | 1999-10-01 | 1231 | yes | other | 3 |
| 1D5R | Crystal Structure of the PTEN Tumor Suppressor | X-ray 2.10 Å | 1999-10-11 | 2968 | no | other | 6 |
| 1EHZ | The crystal structure of yeast phenylalanine tRNA at 1.93 A resolution | X-ray 1.93 Å | 2000-02-23 | 1821 | – | set aside | 3 |
| 1EMA | GREEN FLUORESCENT PROTEIN FROM AEQUOREA VICTORIA | X-ray 1.90 Å | 1996-08-01 | 1866 | no | other | 8 |
| 1F88 | CRYSTAL STRUCTURE OF BOVINE RHODOPSIN | X-ray 2.80 Å | 2000-06-29 | 5267 | no | other | 13 |
| 1FS3 | CRYSTAL STRUCTURE OF WILD-TYPE BOVINE PANCREATIC RIBONUCLEASE A | X-ray 1.40 Å | 2000-09-08 | 1066 | yes | set aside | 3 |
| 1HHO | STRUCTURE OF HUMAN OXYHAEMOGLOBIN AT 2.1 ANGSTROMS RESOLUTION | X-ray 2.10 Å | 1983-06-10 | 2396 | yes | other | 20 |
| 1HK0 | Human GammaD Crystallin Structure at 1.25 A Resolution | X-ray 1.25 Å | 2003-03-05 | 1772 | yes | other | 11 |
| 1HRC | HIGH-RESOLUTION THREE-DIMENSIONAL STRUCTURE OF HORSE HEART CYTOCHROME C | X-ray 1.90 Å | 1994-08-16 | 993 | yes | other | 9 |
| 1HSG | CRYSTAL STRUCTURE AT 1.9 ANGSTROMS RESOLUTION OF HUMAN IMMUNODEFICIENCY VIRUS (HIV) II… | X-ray 2.00 Å | 1995-03-31 | 1686 | yes | not used (worked example of the call-list prompt) | 0 |
| 1HVR | RATIONAL DESIGN OF POTENT, BIOAVAILABLE, NONPEPTIDE CYCLIC UREAS AS HIV PROTEASE INHIBI… | X-ray 1.80 Å | 1994-02-14 | 1890 | yes | other | 10 |
| 1IEP | CRYSTAL STRUCTURE OF THE C-ABL KINASE DOMAIN IN COMPLEX WITH STI-571. | X-ray 2.10 Å | 2001-04-10 | 4710 | no | other | 14 |
| 1IGT | STRUCTURE OF IMMUNOGLOBULIN | X-ray 2.80 Å | 1996-10-25 | 12956 | yes | set aside | 10 |
| 1IRO | RUBREDOXIN (OXIDIZED, FE(III)) AT 1.1 ANGSTROMS RESOLUTION | X-ray 1.10 Å | 1995-12-13 | 858 | no | other | 5 |
| 1K4C | Potassium Channel KcsA-Fab complex in high concentration of K+ | X-ray 2.00 Å | 2001-10-07 | 4534 | yes | other | 7 |
| 1KF1 | Structure and Packing of Human Telomeric DNA | X-ray 2.10 Å | 2001-11-19 | 536 | – | other | 3 |
| 1L2Y | NMR Structure of Trp-Cage Miniprotein Construct TC5b | NMR | 2002-02-25 | 304 | – | other | 2 |
| 1LMB | REFINED 1.8 ANGSTROM CRYSTAL STRUCTURE OF THE LAMBDA REPRESSOR-OPERATOR COMPLEX | X-ray 1.80 Å | 1991-11-05 | 2334 | yes | set aside | 12 |
| 1LYZ | Real-space refinement of the structure of hen egg-white lysozyme | X-ray 2.00 Å | 1975-02-01 | 1102 | yes | other | 3 |
| 1MBN | The stereochemistry of the protein myoglobin | X-ray 2.00 Å | 1973-04-05 | 1260 | yes | other | 10 |
| 1PLC | ACCURACY AND PRECISION IN PROTEIN CRYSTAL STRUCTURE ANALYSIS: RESTRAINED LEAST-SQUARES… | X-ray 1.33 Å | 1992-03-11 | 1657 | yes | other | 5 |
| 1RX2 | DIHYDROFOLATE REDUCTASE (E.C.1.5.1.3) COMPLEXED WITH WITH FOLATE AND NICOTINAMIDE ADENI… | X-ray 1.80 Å | 1996-09-19 | 1503 | no | set aside | 16 |
| 1STP | STRUCTURAL ORIGINS OF HIGH-AFFINITY BIOTIN BINDING TO STREPTAVIDIN | X-ray 2.60 Å | 1992-03-12 | 1001 | yes | other | 10 |
| 1TRN | CRYSTAL STRUCTURE OF HUMAN TRYPSIN 1: UNEXPECTED PHOSPHORYLATION OF TYROSINE 151 | X-ray 2.20 Å | 1995-03-16 | 3705 | yes | other | 18 |
| 1TUP | TUMOR SUPPRESSOR P53 COMPLEXED WITH DNA | X-ray 2.20 Å | 1995-07-11 | 5828 | no | other | 16 |
| 1UBQ | STRUCTURE OF UBIQUITIN REFINED AT 1.8 ANGSTROMS RESOLUTION | X-ray 1.80 Å | 1987-01-02 | 660 | yes | other | 2 |
| 1UDT | Crystal structure of Human Phosphodiesterase 5 complexed with Sildenafil(Viagra) | X-ray 2.30 Å | 2003-05-06 | 2655 | no | other | 12 |
| 1Y26 | A-riboswitch-adenine complex | X-ray 2.10 Å | 2004-11-20 | 1608 | – | other | 9 |
| 2C9V | Atomic resolution structure of Cu-Zn Human Superoxide dismutase | X-ray 1.07 Å | 2005-12-14 | 3043 | yes | set aside | 18 |
| 2CPP | HIGH-RESOLUTION CRYSTAL STRUCTURE OF CYTOCHROME P450-CAM | X-ray 1.63 Å | 1987-04-06 | 3462 | yes | other | 13 |
| 2HHB | THE CRYSTAL STRUCTURE OF HUMAN DEOXYHAEMOGLOBIN AT 1.74 ANGSTROMS RESOLUTION | X-ray 1.74 Å | 1984-03-07 | 4779 | yes | other | 22 |
| 2NWD | Structure of chemically synthesized human lysozyme at 1 Angstrom resolution | X-ray 1.04 Å | 2006-11-14 | 2691 | yes | other | 11 |
| 2OMF | OMPF PORIN | X-ray 2.40 Å | 1995-02-28 | 2827 | yes | set aside | 6 |
| 2P4E | Crystal Structure of PCSK9 | X-ray 1.98 Å | 2007-03-12 | 4776 | no | other | 10 |
| 2PTC | THE GEOMETRY OF THE REACTIVE SITE AND OF THE PEPTIDE GROUPS IN TRYPSIN, TRYPSINOGEN AND… | X-ray 1.90 Å | 1982-09-27 | 2241 | yes | set aside | 12 |
| 3AVE | Crystal Structure of the Fucosylated Fc Fragment from Human Immunoglobulin G1 | X-ray 2.00 Å | 2011-03-04 | 3796 | yes | other | 10 |
| 3EML | The 2.6 A Crystal Structure of a Human A2A Adenosine Receptor bound to ZM241385. | X-ray 2.60 Å | 2008-09-24 | 3757 | yes | other | 11 |
| 3ERT | HUMAN ESTROGEN RECEPTOR ALPHA LIGAND-BINDING DOMAIN IN COMPLEX WITH 4-HYDROXYTAMOXIFEN | X-ray 1.90 Å | 1999-03-30 | 2070 | no | other | 11 |
| 3F9M | Human pancreatic glucokinase in complex with glucose and activator showing a mobile flap | X-ray 1.50 Å | 2008-11-14 | 4065 | no | other | 14 |
| 3K34 | Human carbonic anhydrase II with a sulfonamide inhibitor | X-ray 0.90 Å | 2009-10-01 | 2387 | yes | other | 9 |
| 3KCG | Crystal structure of the antithrombin-factor IXa-pentasaccharide complex | X-ray 1.70 Å | 2009-10-21 | 6669 | yes | set aside | 16 |
| 3NGB | Crystal structure of broadly and potently neutralizing antibody VRC01 in complex with H… | X-ray 2.68 Å | 2010-06-11 | 25808 | yes | other | 5 |
| 3PTB | THE GEOMETRY OF THE REACTIVE SITE AND OF THE PEPTIDE GROUPS IN TRYPSIN, TRYPSINOGEN AND… | X-ray 1.70 Å | 1982-09-27 | 1701 | yes | other | 12 |
| 4INS | THE STRUCTURE OF 2ZN PIG INSULIN CRYSTALS AT 1.5 ANGSTROMS RESOLUTION | X-ray 1.50 Å | 1989-07-10 | 1182 | yes | other | 13 |
| 5CJ6 | Crystal Structure of a Selective Androgen Receptor Modulator Bound to the Ligand Bindin… | X-ray 2.07 Å | 2015-07-14 | 2233 | yes | other | 15 |
| 5EDM | Crystal structure of prothrombin deletion mutant residues 154-167 ( Form I ) | X-ray 2.20 Å | 2015-10-21 | 5005 | yes | other | 13 |
| 5NI1 | CryoEM structure of haemoglobin at 3.2 A determined with the Volta phase plate | EM 3.20 Å | 2017-03-22 | 4579 | yes | set aside | 15 |
| 5UAK | Dephosphorylated, ATP-free human cystic fibrosis transmembrane conductance regulator (C… | EM 3.87 Å | 2016-12-19 | 9232 | no | other | 8 |
| 6HPO | Crystallographic structure of the catalytic domain of Human Phenylalanine Hydroxylase (… | X-ray 1.67 Å | 2018-09-21 | 2880 | no | set aside | 6 |
| 6M7H | Structure of calmodulin with KN93 | X-ray 1.60 Å | 2018-08-20 | 1311 | yes | other | 17 |
| 6TC2 | Monoclinic human insulin in complex with p-coumaric acid | X-ray 1.36 Å | 2019-11-04 | 5094 | yes | set aside | 16 |
| 6THA | Crystal structure of human sugar transporter GLUT1 (SLC2A1) in the inward conformation | X-ray 2.40 Å | 2019-11-19 | 3556 | no | set aside | 7 |
| 6VXX | Structure of the SARS-CoV-2 spike glycoprotein (closed state) | EM 2.80 Å | 2020-02-25 | 23694 | no | other | 8 |
| 7A4M | Cryo-EM structure of mouse heavy-chain apoferritin at 1.22 A | EM 1.22 Å | 2020-08-20 | 3177 | yes | other | 9 |
| 8C86 | Crystal structure of human transthyretin in complex with 3-O-methyltolcapone analogue 2 | X-ray 1.10 Å | 2023-01-18 | 4150 | yes | other | 22 |
| 8CE0 | N-terminal domain of human apolipoprotein E | X-ray 1.75 Å | 2023-02-01 | 1335 | yes | set aside | 12 |
| 8EPH | Crystal structure of human coagulation factor IXa (S195A), apo-form, DES-GLA | X-ray 1.88 Å | 2022-10-05 | 5564 | yes | other | 19 |
| 8K7F | Crystal structure of human lysosomal alpha-galactosidase A in complex with (2R,3S,4R,5R… | X-ray 1.98 Å | 2023-07-26 | 7126 | no | set aside | 13 |
| 8PI2 | Native alpha-1-antitrypsin at 1.5 Angstrom (Cys232Ser) | X-ray 1.48 Å | 2023-06-20 | 6156 | yes | other | 10 |
| 9F69 | Crystal structure of human triose phosphate isomerase with methyl malonic acid ligand | X-ray 1.17 Å | 2024-04-30 | 4040 | no | other | 10 |
| 9FB2 | Gcase in complex with small molecule inhibitor 1 | X-ray 1.14 Å | 2024-05-11 | 4971 | no | other | 15 |
| 9GIO | Crystal structure of the VHL-EloC-EloB complex with a covalent compound bound to C77 of… | X-ray 1.49 Å | 2024-08-19 | 3043 | no | other | 15 |
| af-p04637-f1-model_v6 | AlphaFold DB model of Cellular tumor antigen p53 (TP53, Homo sapiens) | AlphaFold prediction | 2025-08-01 | 3060 | no | other | 5 |
| af-p07320-f1-model_v6 | AlphaFold DB model of Gamma-crystallin D (CRYGD, Homo sapiens) | AlphaFold prediction | 2025-08-01 | 1459 | no | other | 3 |
| af-p0dp23-f1-model_v6 | AlphaFold DB model of Calmodulin-1 (CALM1, Homo sapiens) | AlphaFold prediction | 2025-08-01 | 1174 | no | other | 3 |
| af-p61626-f1-model_v6 | AlphaFold DB model of Lysozyme C (LYZ, Homo sapiens) | AlphaFold prediction | 2025-08-01 | 1157 | no | other | 2 |
| af-p68871-f1-model_v6 | AlphaFold DB model of Hemoglobin subunit beta (HBB, Homo sapiens) | AlphaFold prediction | 2025-08-01 | 1131 | no | other | 10 |

### S3.2 The variant list, step by step

We use *missense* variants only: one amino acid replaced by another. Throughout, the
*classification* of a variant means ClinVar's aggregate germline classification on a variation
record, the record whose accession begins with VCV. ClinVar keeps germline classifications
(of variants present in every cell of a person, inherited or newly arisen) apart from somatic
ones (of variants that arise in a tumour); we use the germline one. A variation record
is usually about one change at the level of DNA, and different DNA changes can give the same
amino-acid change, so one amino-acid change can have several records.
74 of the variants that we keep have more than one record
that passes steps 2, 3a and 3b of Table S4 (where a variant has single-nucleotide records, only these are counted).

**Table S4. The variant list in three steps.** Counts are of variants (amino-acid changes)
removed and left. The tests 3a to 3c are applied in this order. Section 3.1 of the paper
gives the first and the last count, and states the rule as four conditions on one record.
A *matching record* (step 2) that is of the named gene (3a), is not a haplotype (3b) and
states its assertion criteria (3c) is a *qualifying record*, the term of the paper.

| Step | Rule | Removed | Left |
|:--|:----------------------------------|---:|---:|
| 1 | Single-residue missense variants of the 27 proteins that UniProt reports as pathogenic or likely pathogenic, with ClinVar as a source | | 3,352 |
| 2 | Keep if a ClinVar variation record, reached through UniProt's cross-references, lists the same amino-acid change at that position and has the aggregate germline classification "Pathogenic", "Likely pathogenic" or "Pathogenic/Likely pathogenic" (a *matching record*) | 657 | 2,695 |
| 3a | Remove if no matching record is of the gene that the request names | 44 | |
| 3b | Remove if every matching record of that gene is a haplotype (two changes on one chromosome) | 35 | |
| 3c | Remove if every remaining matching record has the review status "no assertion criteria provided" | 216 | 2,400 |

*The rule in one sentence.* A variant is kept if at least one ClinVar record that lists it is
classified as pathogenic or likely pathogenic, is of the gene that the request names,
describes that change alone, and states its assertion criteria.

*Step 1.* The candidates come from UniProt's variant annotation of the
27 proteins. The position is that of the UniProt canonical sequence.

*Step 2.* We examined only the ClinVar records that UniProt cross-references for a variant;
we did not search ClinVar itself. UniProt's annotation can carry a pathogenic label where ClinVar's aggregate
classification does not; we observed this for 657 candidates
(20%), most of which ClinVar classifies as "Conflicting
classifications of pathogenicity" or "Uncertain significance". A candidate is kept only if a
ClinVar record, reached through UniProt's cross-references to ClinVar, lists the same
amino-acid change at the same position among its protein changes and is classified
"Pathogenic", "Likely pathogenic" or "Pathogenic/Likely pathogenic". ClinVar lists the protein
change of a record once for each transcript of the gene. A record matches if any one of these
names equals our amino-acid change and position; we did not check which transcript that name
is counted on. We therefore rely on at least one reference protein of the record being numbered as
the UniProt canonical sequence is at that position. We also did not look for further records
of the same amino-acid change that carry another classification: one qualifying record is
enough, and ClinVar may hold a second record that disagrees with it.

*How the names in the requests relate to the HGVS nomenclature.* Names with "p." follow the
protein-level style of the HGVS nomenclature, the standard of the Human Genome Variation
Society for naming variants [1, 2], but they are not complete
HGVS descriptions. A complete description puts a reference sequence with its version number
before the "p."; for a protein change this is a protein accession of RefSeq or Ensembl
(beginning with NP_ or ENSP). A UniProt accession, which 46
requests state, is not such a reference sequence. HGVS also prefers the three-letter form,
and it puts parentheses around a protein change that is predicted from the DNA change and
was not observed in the protein. Our requests write the protein change without parentheses
(p.W82R or p.Trp82Arg).

*How ClinVar names a record.* ClinVar states each change on a *transcript*, a reference
sequence of one messenger RNA of the gene. For the running example the title of the record
is NM_000239.3(LYZ):c.244T>C (p.Trp82Arg): nucleotide 244 of the coding sequence
of transcript NM_000239.3, counted from the A of the start codon ATG, changes
from T to C, and the protein change follows in
parentheses. This is the format of ClinVar's titles; we take the protein change in it to be
the consequence predicted from the DNA change. A gene can have several transcripts, and they
can number the protein differently, so a ClinVar record lists the protein change once for
each transcript. We accept a record if any one of these names equals our amino-acid change
and position (step 2). We did not check which transcript that name is counted on; we take
its position to be that of the UniProt canonical sequence (Section S14.2).

*What a request says about the classification.* ClinVar classifies DNA-level records, each
for a stated condition. A request attaches the classification to the protein-level name and
names no condition: it means that at least one record of this amino-acid change, of the
named gene, carries that classification. Where the records behind one request carry different
values, the request says "pathogenic or likely pathogenic" (7
requests); 21 requests say "pathogenic/likely pathogenic", which is
ClinVar's own aggregate value on their records.

*Step 3.* A request says, in ClinVar's own word for the record, that the variant of a named
gene is classified as pathogenic, as likely pathogenic, or as pathogenic/likely pathogenic
("the *LYZ* variant p.W82R is classified as pathogenic in ClinVar"). The classification must
therefore rest on a record of that gene, about that one change, with stated criteria. In step
3a the other gene is nearly always one that encodes the same protein (*CALM2* or *CALM3* for
calmodulin, *HBA2* for alpha-globin). In step 3b the record describes two changes on one
chromosome and says nothing about either alone. In step 3c no submitter stated the criteria
behind the classification.

*Two variants were handled individually, outside these rules.* One variant removed in step 3c
is used all the same, in 1 task per track: lysozyme p.Ile74Thr
(I56T in the older literature), one of the first two variants reported to cause hereditary
lysozyme amyloidosis [3]. It is outside the 2,400. Its
request says that the variant "is classified as pathogenic in
ClinVar", which is what the record says; the record states no assertion criteria, and this
task is therefore an exception to the rule above. One variant inside the
2,400 is never asked about: APOE p.Arg154Ser (R136S in the older literature,
the Christchurch variant). ClinVar's pathogenic record for it concerns a disorder of blood
lipids, while the variant is widely known for a reported protective effect in Alzheimer's
disease, so a request that calls it pathogenic would mislead.

*Well-known variants tried first.* Within the pool, the generator picks variants by seeded
random choice. For 9 proteins a list written by hand before
generation names well-known variants that are tried first, and used if they are in the pool
(or are the exception above) and observed in the structure: *CFTR* p.G551D; *GBA1* p.N409S; *HBB* p.E7V; *HRAS* p.G12S; *LYZ* p.I74T; *SERPINA1* p.E366K; *SOD1* p.A5V; *TP53* p.R175H, p.R248Q, p.R273H; *TTR* p.V50M. The list
decides which variant is asked about, never what the answer is.

*Traditional names.* A traditional name is used in 13 requests per
track. 7 of these names differ from the UniProt number by the
initiator methionine alone (by 1), 4 by a signal peptide, and
2 by a signal peptide and a propeptide; each request
says which.

*Proteins without a task.* Tasks exist for 25 of the
27 proteins. The other 2
are, by gene name, CA2 and TPI1. For *TPI1* (triosephosphate isomerase)
the steps above left no variant. For *CA2* (carbonic anhydrase 2) they left one, at the first
residue of the sequence, which the panel structure does not contain; a task needs a residue
that is observed in the structure.

*Proteins and structures.* The 25 proteins give tasks on
31 structures. 6 proteins have tasks
on more than one structure, and 2 haemoglobin entries serve
two proteins each, because they hold both the alpha and the beta chain.

*Dates.* The variant lists and the classifications of step 2 were read from UniProt and
ClinVar on 12 November 2026. The records were read again on
16 November 2026, with their kind, gene, classification and review status; step
3 and the wording of the requests rest on that second reading.

## S4. Grading rules in full

### S4.1 Facts

The drawn state is cut into facts, each of weight 1.

- **Facts about atoms.** An atom's drawing is the set of its styles (a style is a
  representation type with a colour and an opacity). All atoms with the same set form one fact.
- **Facts about the scene**, when present: each label text with the atoms it is attached to; each
  tooltip text with its atoms; the camera target (the atoms it frames); each distance line or
  other drawn primitive; a request that the viewer compute and draw non-covalent interactions
  around some atoms; the structure type when it is not the first deposited coordinate set (an
  assembly, or another coordinate set of the entry); the background colour when it is not the default.

The structure is the frame in which facts are stated, not a fact. A file that an answer
downloads and never draws changes nothing on screen and is not counted. A second structure
that is drawn is unrequested drawing.

### S4.2 F1

Recall is the mean, over the reference's facts, of how much of each the answer has. Precision
is the mean, over the answer's facts, of how much of each the reference has. F1 is their
harmonic mean. Two drawn states are compared, that of the reference and that of the answer;
*the other* below means the other of these two. How much of a fact the other drawn state has:

- *Fact about atoms*: the mean over its atoms of the share of the atom's styles that the
  other also has. A style that the other has with the same representation type and another
  colour or opacity counts half. An atom that the other does not draw counts 0. Styles that
  the other has in addition do not lower this number; they lower the number computed in the
  other direction.
- *Label, tooltip, interaction request*: the share of the atoms carrying it that carry the
  same in the other.
- *Camera target*: the overlap (intersection over union) of the two targets, as whole
  residues.
- *Primitive, structure type, background*: 1 if the other has the same, else 0.

An answer that draws nothing scores 0 on every score when the reference draws something.

### S4.3 Target score

The target score, from 0 to 1, is how exactly the answer marks out the requested atoms. It is 1 (*target-right*) when three things hold: the target atoms carry the requested style; no other atom carries that style; and no second representation is drawn on target atoms alone. Any other drawing, such as a cartoon of the protein, is ignored. The counts below make this exact.

The *target's drawing* is the set of the reference's styles that lie wholly inside the target
atoms (in the running example the yellow spacefill spheres of the residue; a cartoon of the
whole chain that passes through the residue is not part of it). It is
cut into facts as above. For each fact, counting items (one item is one style on one atom):

- *wanted*: the reference's items;
- *credit*: 1 for each wanted item that the answer has, ½ for each that the answer draws in
  the right representation with another colour or opacity, in a style confined to the target
  (the right residue as blue sticks where red sticks were asked for). The right
  representation in another colour in a style that runs on beyond the target, such as a grey
  cartoon of the whole chain, does not single the target out: it earns no credit and is not
  counted as attempted or as spill;
- *attempted*: the wanted items that the answer drew in the right representation, in any
  colour or opacity, in a style confined to the target;
- *spill*: items outside the target that belong to a style of the answer (one representation
  in one colour and opacity) which also earned credit on the target, where the reference
  draws no such thing. The style is the answer's own: if it drew the target in red where
  yellow was asked, its red items outside the target are spill. The requested representation
  drawn outside the target in a separate style of another colour is not spill but
  unrequested context;
- *extra*: items on the target from a style of the answer that is confined to the target, in
  a representation type that the reference does not draw there.

Target recall = credit / wanted. Target precision = credit / (attempted + spill + extra). The
target score is the harmonic mean of the two, each averaged over the target's facts and over
the facts about the scene that touch the target atoms (a label on the target, for example).
A target with one fact, as in the running example, needs no averaging. The three rules for extra drawing follow from these counts. *Spill*: the answer repeats, on
atoms outside the target, the style that it drew on the target in the requested
representation, whatever its colour (red spacefill on the whole chain, where yellow spacefill
on one residue was asked for, is spill); the items count against target precision. *Extra
on the target*: a style of the answer in another representation that is confined to the
target; its items count against target precision. *Unrequested context*: any other style of
the answer that is not confined to the target (a cartoon or a surface of the chain, of the
whole chain or of part of it) is ignored, even if it would hide the target in a picture; F1
and task success count it. Table S1 gives the score of one example of each rule. The line
between the second and the third rule is whether the style is confined to the target. It is a
convention: a second representation on the target alone is read as part of the answer to "how
should these atoms be drawn?", and a style that also covers other atoms is read as background.
Rows S9 and S10 of Table S1 show the two cases. Row S9 by hand: the target has
24 atoms and one requested style, so wanted, credit and attempted are each
24; the added ball-and-stick is confined to the target, so extra is
24; target precision is 24/48
= 0.50, target recall is 1, and the target score is
0.67. In row S10 the ball-and-stick also covers the two neighbours,
is not confined to the target, and enters no count.

Tasks without a stored target are of two kinds (Section 4.2 of the paper). A single request
without one, such as a change of the background colour, uses everything the reference draws or
changes as its target. A follow-up task without one, in which the edit takes something away,
changes or restores a setting of the whole view, or needs no change, has no target score, and averages leave it out: there are no atoms
"drawn as asked", and to use everything the reference draws would give full marks to the
start state returned unchanged.

### S4.4 Accepted answers and follow-up turns

A task may list further right answers. An answer is graded against the reference and each of
them, and the best result counts (a success first, then the highest F1). The target score is
the best over the reference and all of them, whichever has the best F1: they differ only in
what the request leaves open. A name-resolution
task lists the entries that match the named protein. The list was frozen on
13 November 2026 from the web services of the RCSB PDB (the US member site of the
Protein Data Bank): it holds every current PDB entry
in which a chain is aligned to the UniProt accession of the named protein over at least
50 residues in total, or over at least half of the UniProt sequence if
that is shorter. Where the request names several proteins, a ligand or bound DNA, the entry
must hold all of them. The references of this category select by kind (the polymer, the
protein, the nucleic acid) or by the identifier of a compound, never by chain identifier or
residue number, so the same selections can be evaluated on any entry. An answer on another
listed entry that is in the structure panel (3 such entries
exist) is graded on drawn state: the reference's selections and the answer's are both
resolved on the atom table of that entry. Where the entry is outside the structure panel,
selections are compared as written (Section S4.8), and F1, task success and the target score
all come from that comparison. A follow-up task gives a start
state and an edit request; the answer is the complete new scene or call list, and only the
drawn state it results in is graded. If the right answer is to change nothing, the reference is the start
state.

### S4.5 What the viewer draws (scene track, Mol\* 5.9.0)

Each rule was read back from the running viewer.

- Ball-and-stick, line, spacefill and surface representations draw every atom of their
  component. Cartoon, backbone and putty draw polymer residues, and only those whose trace atom
  (Cα of an amino acid, O3′ of a nucleotide) is in the component.
- A cartoon, backbone or putty requested on a component with no polymer atoms is drawn as
  ball-and-stick, and is graded as that.
- A component whose selector matches no atom is not created.
- A representation with no colour is white. Colour nodes apply in order, later over earlier.
  A colour value that is not a known name or a hexadecimal code makes Mol\* reject the scene.
- Two representations of different types on overlapping components are both drawn; the atom
  carries both styles.
- Of two opaque representations of the same type on the same atoms, only one is seen: the one
  listed first or, if their sizes differ, the larger. The other is not graded as drawn. So a
  grey cartoon of the chain followed by a green cartoon of one stretch of it, as a component
  of its own, is a cartoon that is grey all over. A surface is the exception, and so is a
  representation with opacity below 1. The rule was measured by counting pixels in the
  running viewer for every representation type, and the format guide states it.
- An AlphaFold model has one file address, that of the AlphaFold Protein Structure Database
  with the model version of the panel. The same file name on another host, or without the
  version, is not served, so an answer that names it is unshowable.
- Author and label numbering are different columns and are never pooled.
- A reference that colours "by chain" is matched by the same colour theme, or by an answer
  that gives every chain one colour of its own, all different.

Colour. Two colours count as the same if their red, green and blue values (0 to 255) each
differ by at most 32; the distance between two colours is the largest of
these three differences. Requests use a palette of 19 named colours. Its
two closest colours (plum and hotpink) are 55 apart. In
the pilot run, 2,303 colour values in answers could be compared with
a requested colour. Of these, 2,227 were exactly the requested colour, and
each of the other 76 was at least 58 away
from it, so the tolerance decided no case.

Not graded on the scene track: metadata, the host of the structure file, the order of
children (except between two coincident representations, above), representation size and surface kind, the appearance of labels and primitives, explicit camera
numbers.

### S4.6 What the viewer does (call-list track, PDBe Mol\* 3.3.2)

The grader replays the calls in order with a port of the viewer's own code paths (selection,
colouring, representation, visibility, reset). The facts of the drawn state that a call list
ends in are its differences from the default view of the same structure, that is, from a
*bare load*, a load with no further call:

| Fact | One per |
|:---|:---|
| atoms | each group of atoms whose drawing a colouring call changed, now drawn the same way |
| scene | the effect of the viewer's global representation setting and of the hide switches on all other atoms |
| focus, highlight, tooltip | the residues framed, the residues highlighted, each tooltip text with its atoms |
| assembly, preset, option, canvas | the assembly identifier, the load preset, each non-default option, each non-default canvas setting |

A bare load has no facts and scores 0, unless a bare load is the reference. Two details differ
from the scene track. A fact about atoms scores the share of its atoms that end up looking
exactly the same in the other drawn state; atoms that reference and answer both changed but
that look different count half. The target score is computed on the changes from a bare load
on the target atoms (a style added, or a default style removed), with the same counts of
wanted, credit, attempted, spill and extra as on the scene track. Selections in
UniProt numbering are resolved through the frozen SIFTS tables; the viewer reads the same
mapping from the structure file that PDBe distributes. A PDB identifier must be written in
lower case: the viewer puts it into the file address as written, PDBe serves its files under
lower-case names only, and a load with the identifier in upper case shows nothing, as
measured in the running viewer against PDBe's server. Such an answer loads nothing and
scores 0. The format guide says so.

### S4.7 Outcomes

**Table S5. The outcome of an answer and how it is scored.** *As graded*: the answer receives
the scores that the grader computes. Strict averages count every answer with the score in the
last column; valid-only averages count the answers with outcome "valid". *Class*: the three
classes of Section 4.4 of the paper. An answer that was cut off at the token limit gets the
outcome of the text that arrived and is counted apart from other invalid answers in the outcome
tables.

| Track | Outcome | Class | Meaning | Score |
|:---|:---|:---|:---|:---|
| both | invalid JSON | unshowable | the answer contains no parseable JSON of the right outer shape | 0 |
| scene | not a scene | unshowable | JSON, but not a scene tree | 0 |
| scene | rejected by the viewer | unshowable | a scene tree that the validation of Mol\* 5.9.0 rejects | 0 |
| scene | structure failed to load | unshowable | a well-formed scene that names a file which Mol\* cannot load: a web page in place of a structure file, a file on an unknown host, or a file read in the wrong format | 0 |
| scene | valid | valid | Mol\* accepts the scene and can load its file | as graded (0 on every score if the entry is not one that the task accepts) |
| call list | not valid | schema-breaking | a JSON list that breaks the call schema (unknown call, wrong field type) | as graded: the replay ignores what the viewer would ignore |
| call list | valid | valid | a call list that fits the schema | as graded |

### S4.8 Known limits of the grader

- **Assemblies.** Atom tables hold the first coordinate set of the deposited unit. An assembly is a fact (its
  identifier), and atoms are compared on the deposited unit. Selections of single symmetry
  copies are not modelled.
- **Other coordinate sets of an entry that has several** are compared on the atoms of the
  first set, and the index of the coordinate set is a fact.
- **Entries outside the structure panel** have no atom table. An answer on such an entry (possible only
  in the name-resolution category) is compared as written: two selections are equal only if
  spelled the same way.
- **Colour themes** other than colouring by chain or by entity are matched only by the same
  theme.
- **Distance lines.** The target score does not notice a missing distance line. Lines, labels
  and the camera target were not read back from Mol\*; they are compared as declared.
- **Lone ions.** 8 tasks, half of them on each track, ask for a
  metal ion as a sphere, and the reference draws it as spacefill. An answer that draws the ion as ball-and-stick uses another
  representation and, by the general rule, receives a target score of 0, although a single
  atom looks much the same in both.
- **The file that PDBe Mol\* fetches.** The atom tables are built from the archive file of
  each entry, and the replay in PDBe Mol\* loaded that file. Left to itself, the viewer
  fetches PDBe's own copy of the entry, which also carries the SIFTS mapping; the mapping
  tables are read from that copy. The atom records of the two copies were not compared.
- **Call-list actions that one host ignores.** The call-list track grades what each call does
  in PDBe Mol\* 3.3.2. The notebook widget that hosts this viewer for Python users (ipymolstar
  0.1.0) has no handler for four of the actions (camera focus, setting the highlight colour,
  clearing the highlight and clearing the selection); there they do nothing.
- **Call-list track.** Four options fetch data from live services (superposition of related
  structures, the close-up view of one ligand, annotations from databases, experimental
  density maps). They are compared as declared settings, and so is lighting. Camera focus,
  highlight and UniProt-numbered selections were not read back from the viewer. Which atoms
  are polymer, ligand, ion or water comes from tables filled by Mol\* 5.9.0, whereas PDBe Mol\*
  3.3.2 carries an older Mol\*; a bare load of 73 entries was
  compared with the viewer, and the two differences found are modelled as measured.
- **A second cartoon.** An answer that recolours a stretch by adding a second coloured cartoon
  after the cartoon of the whole chain changes nothing that is seen (Section S4.5), and is
  graded as the first cartoon alone.

## S5. The control set by kind

The control set has 2,175 controls on the structures of the structure panel, each a reference
and one answer: 1,155 on the scene track (150
identical, 500 equivalent, 505 wrong) and
1020 on the call-list track (150 identical,
425 equivalent, 445 wrong). The verdict of each
control is known from how its answer was made.

Read-back from the viewers. Scene track: the read-back was run on the control set as it then
stood, 1,155 scene controls. For
910 of them both scenes were loaded in Mol\*
5.9.0 and their drawing read back; in all of them the viewer agreed with
the verdict. The other 245 are of kinds that cannot be read back
(camera target, label text, colouring by chain, assembly, another entry).
Scene controls added since then, and not read back in the viewer: 0. In the same run the grader's resolved state equalled the viewer's for all
1,545 scenes, and 3,926 single
representations probed across the panel were drawn as the grader predicts. Call-list track:
the replay was run on the control set as it then stood,
1020 call-list controls of 46
kinds. A sample of 150 controls was drawn by taking one control
from each kind in turn, and again, until that number was reached. Each control has two call
lists, its reference and its answer, so the sample holds
300. The 27 that select
by UniProt number were left out, 3 could not be run by
our replay script, and 3 load nothing by the grader's
rule for file addresses, which a replay from local files cannot test (Section S4). The other 267 call lists were replayed in PDBe
Mol\* 3.3.2, and every one ended in the state that the grader
computes. Call-list controls added since then: 0. The
record of the replay holds the number of call lists; the number of controls in the sample was
worked out by script from that record and from the control set of the same day.
The call-list controls use 74 structures: the
4 entries that hold only DNA or RNA
(1BNA, 1EHZ, 1KF1 and 1Y26) have none, because each call-list control is built around a
protein residue.

**Table S6. Every kind of control.** *Controls*: number of controls of this kind. *Graded as
success*: controls that the grader counts as task success; this must equal *Controls* for
kinds that must pass and 0 for kinds that must fail. *Earlier grader*: the same count for the grader that
this work replaces on that track, with a score of exactly 1 read as success.

**Scene track.**

| Verdict known from construction | Kind of control | Controls | Graded as success | Graded as success by the earlier grader |
|:-----|:----------------------|---:|---:|---:|
| must pass (equivalent) | selector 'all' instead of 'polymer' under a cartoon (a cartoon draws polymer only) | 20 | 20 | 1 |
| must pass (equivalent) | a chain's cartoon selected by author chain id, label chain id or entity id | 20 | 20 | 2 |
| must pass (equivalent) | reference colours by the chain-id theme; the answer gives each chain its own colour | 20 | 20 | 0 |
| must pass (equivalent) | components, and the keys inside nodes, in another order | 20 | 20 | 20 |
| must pass (equivalent) | a colour given as #rrggbb (lower or upper case) instead of its name | 20 | 20 | 0 |
| must pass (equivalent) | defaults stated explicitly: opacity 1, colour selector 'all', model_index 0, size_factor 1 | 20 | 20 | 0 |
| must pass (equivalent) | an extra component that selects no atoms (nothing is drawn for it) | 20 | 20 | 0 |
| must pass (equivalent) | a full state with metadata, and the same entry from another server or as BinaryCIF | 20 | 20 | 13 |
| must pass (equivalent) | the focus node on its own component with the same selector | 20 | 20 | 20 |
| must pass (equivalent) | 'grey' instead of 'gray' | 20 | 20 | 20 |
| must pass (equivalent) | a residue range in label numbering instead of author numbering | 20 | 20 | 20 |
| must pass (equivalent) | a residue addressed by label chain and number instead of author chain and number | 20 | 20 | 20 |
| must pass (equivalent) | a ligand selected by residue name, or each copy by author chain and number | 20 | 20 | 20 |
| must pass (equivalent) | one cartoon with a colour child for one chain, or one cartoon component per chain | 20 | 20 | 0 |
| must pass (equivalent) | three residues in one component (a selector list) or in three components | 20 | 20 | 20 |
| must pass (equivalent) | a stretch in a colour of its own, drawn as a component of its own that is listed before the grey drawing of the whole polymer in the same representation type: the first one listed is the one seen (pixels counted in Mol*, tests/controls/overlap_evidence.json) | 20 | 20 | 0 |
| must pass (equivalent) | a colour that a later colour node replaces (the last one wins) | 20 | 20 | 0 |
| must pass (equivalent) | one residue range written as two adjacent ranges in two components | 20 | 20 | 20 |
| must pass (equivalent) | six residues listed one by one instead of an author-number range | 20 | 20 | 20 |
| must pass (equivalent) | a residue's ball-and-stick selected atom by atom instead of as a residue | 20 | 20 | 20 |
| must pass (equivalent) | a cartoon asked for on a ligand or ion: Mol* draws ball-and-stick instead | 20 | 20 | 0 |
| must pass (equivalent) | a cartoon on the C-alpha atoms of a range instead of on the residues | 20 | 20 | 0 |
| must pass (equivalent) | the request states no colour for the cartoon (the reference has no colour node there): the answer gives it a palette colour | 20 | 20 | 0 |
| must pass (equivalent) | a stretch of the cartoon is to be coloured and the rest has no stated colour: the answer colours the rest in another palette colour | 20 | 20 | 0 |
| must pass (equivalent) | another entry's file is downloaded and parsed as well, and nothing of it is drawn | 20 | 20 | 0 |
| must pass (identical) | the answer is the reference itself | 150 | 150 | 150 |
| must fail (wrong) | 'all' instead of 'polymer' under ball-and-stick (waters and ligands are drawn too) | 20 | 0 | 0 |
| must fail (wrong) | the right scene on an AlphaFold model address that does not exist: the file name on RCSB's host, without its model version, with an old version, or in lower case (the viewer shows nothing) | 5 | 0 | 3 |
| must fail (wrong) | the biological assembly is loaded where the deposited coordinates was asked for | 20 | 0 | 0 |
| must fail (wrong) | the author residue number written in the label-number field (structures where they differ) | 20 | 0 | 0 |
| must fail (wrong) | two chains' colours the wrong way round | 20 | 0 | 0 |
| must fail (wrong) | the structure is loaded and nothing is drawn | 20 | 0 | 0 |
| must fail (wrong) | something that was not asked for is drawn as well | 20 | 0 | 0 |
| must fail (wrong) | the right scene on a source Mol* cannot read: the mmCIF file parsed as BinaryCIF, the entry's web page instead of its file, or a bare file name (the viewer shows nothing) | 20 | 0 | 13 |
| must fail (wrong) | the camera focus is on another residue, or absent | 20 | 0 | 0 |
| must fail (wrong) | the label residue number written in the author-number field (structures where they differ) | 20 | 0 | 0 |
| must fail (wrong) | the residue label has another text | 20 | 0 | 0 |
| must fail (wrong) | one requested component is not drawn | 20 | 0 | 0 |
| must fail (wrong) | a neighbouring shade outside the tolerance (lightgray for gray, darkred for red, ...) | 20 | 0 | 0 |
| must fail (wrong) | reference colours by chain; the answer paints every chain the same colour | 20 | 0 | 0 |
| must fail (wrong) | a stretch is to be coloured: the answer draws the whole polymer in grey and then the stretch again, same representation type, in the colour. The second drawing lies exactly under the first and is not seen: the picture is grey all over (pixels counted in Mol*, tests/controls/overlap_evidence.json) | 20 | 0 | 0 |
| must fail (wrong) | a residue range that stops three residues early | 20 | 0 | 0 |
| must fail (wrong) | the neighbouring residue is highlighted | 20 | 0 | 0 |
| must fail (wrong) | only the side chain is drawn where the whole residue was asked for | 20 | 0 | 0 |
| must fail (wrong) | the UniProt residue number used as the author number (structures with an offset) | 20 | 0 | 0 |
| must fail (wrong) | a stretch of the cartoon is to be coloured and the rest has no stated colour: the answer colours the whole cartoon in the stated colour, so nothing stands out | 20 | 0 | 0 |
| must fail (wrong) | the same residue number in another chain | 20 | 0 | 0 |
| must fail (wrong) | the highlight in another palette colour | 20 | 0 | 0 |
| must fail (wrong) | the same scene on another structure | 20 | 0 | 0 |
| must fail (wrong) | another copy of the ligand than the one asked for | 20 | 0 | 0 |
| must fail (wrong) | a transparent surface with another opacity, or opaque | 20 | 0 | 0 |
| must fail (wrong) | the highlight in another representation type | 20 | 0 | 0 |

**Call-list track.**

| Verdict known from construction | Kind of control | Controls | Graded as success | Graded as success by the earlier grader |
|:-----|:----------------------|---:|---:|---:|
| must pass (equivalent) | struct_asym_id (label chain) instead of auth_asym_id for the same chain | 20 | 20 | 17 |
| must pass (equivalent) | auth_residue_number instead of auth_seq_id | 20 | 20 | 20 |
| must pass (equivalent) | a colour as #rrggbb or as an {r,g,b} object instead of its name | 20 | 20 | 0 |
| must pass (equivalent) | an entity id instead of the entity's only chain | 20 | 20 | 0 |
| must pass (equivalent) | the same entry loaded by URL (PDBe's updated file) instead of by its id | 20 | 20 | 0 |
| must pass (equivalent) | focus: true inside the color call, or a separate focus action | 20 | 20 | 0 |
| must pass (equivalent) | settings that do not interact, in another order | 20 | 20 | 20 |
| must pass (equivalent) | struct_asym_id + residue_number (label) instead of auth_asym_id + auth_seq_id | 20 | 20 | 10 |
| must pass (equivalent) | a ligand by residue name, or each copy by author chain and number | 20 | 20 | 0 |
| must pass (equivalent) | steps that change nothing are added | 20 | 20 | 0 |
| must pass (equivalent) | two residues in one color call, or in two calls with keep_colors | 20 | 20 | 0 |
| must pass (equivalent) | a wrong color call followed by the right one (only the final state counts) | 20 | 20 | 0 |
| must pass (equivalent) | six residues one by one instead of a start/end range (label or author numbers) | 20 | 20 | 0 |
| must pass (equivalent) | the selections of one call in another order | 20 | 20 | 20 |
| must pass (equivalent) | sideChain: true instead of representation: ball-and-stick | 20 | 20 | 0 |
| must pass (equivalent) | set_property visual_style instead of set_visual_style | 20 | 20 | 0 |
| must pass (equivalent) | tooltip text differing only in case and repeated spaces | 20 | 20 | 20 |
| must pass (equivalent) | on an AlphaFold DB model, a residue by UniProt accession and number instead of author numbering (the model file carries the SIFTS columns) | 5 | 5 | 0 |
| must pass (equivalent) | a residue by UniProt accession and number, or every mapped copy by author numbering | 20 | 20 | 0 |
| must pass (equivalent) | a grey cartoon and a coloured ligand are asked for: the answer leaves the cartoon to the viewer's default view and paints the ligand (water and other components stay on screen, which the request does not mention) | 20 | 20 | 0 |
| must pass (equivalent) | the same request answered on the default view with the waters hidden, which nobody asked for: the task accepts the cartoon style (no water drawn) and the default view (water drawn), so the state in between is right too (the task's free_hide) | 20 | 20 | 0 |
| must pass (equivalent) | a grey cartoon and a residue as coloured ball-and-stick are asked for: the answer colours the residue and adds the ball-and-stick in the same colour, the form the API prompt's own example teaches (the residue's stretch of cartoon takes the highlight colour) | 20 | 20 | 0 |
| must pass (identical) | the answer is the reference itself | 150 | 150 | 149 |
| must fail (wrong) | the right calls on an AlphaFold model address that does not exist (the file name on RCSB's host, without its model version, with an old version, or in lower case): nothing loads | 5 | 0 | 0 |
| must fail (wrong) | the author residue number given as residue_number, which is label numbering | 20 | 0 | 15 |
| must fail (wrong) | the structure is loaded and nothing else is done | 20 | 0 | 0 |
| must fail (wrong) | color given where representationColor was needed: the added sticks stay element-coloured | 20 | 0 | 20 |
| must fail (wrong) | a second color call without keep_colors wipes the first colour | 20 | 0 | 0 |
| must fail (wrong) | something that was not asked for is done as well | 20 | 0 | 0 |
| must fail (wrong) | the focus is on another residue, or absent | 20 | 0 | 0 |
| must fail (wrong) | the label residue number given as auth_seq_id | 20 | 0 | 0 |
| must fail (wrong) | one requested step is left out | 20 | 0 | 0 |
| must fail (wrong) | a residue range that stops three residues early | 20 | 0 | 20 |
| must fail (wrong) | the neighbouring residue is coloured | 20 | 0 | 0 |
| must fail (wrong) | the global style is set after colouring, which wipes it | 20 | 0 | 20 |
| must fail (wrong) | the UniProt residue number used as the author number (structures with an offset) | 20 | 0 | 0 |
| must fail (wrong) | a residue by UniProt accession and number on RCSB's mmCIF loaded by URL: that file has no SIFTS columns, so the viewer selects nothing | 20 | 0 | 0 |
| must fail (wrong) | the default-view answer to 'grey cartoon, ligand in <colour>' without the grey: the cartoon keeps the viewer's chain colours, and grey was stated | 20 | 0 | 0 |
| must fail (wrong) | the default-view answer to 'grey cartoon, ligand in <colour>' with the ligand in another palette colour: what the request states still has to match | 20 | 0 | 0 |
| must fail (wrong) | the default-view answer to 'grey cartoon, residue as coloured ball-and-stick' with the polymer hidden: a free hide toggle never covers what was asked for | 20 | 0 | 0 |
| must fail (wrong) | the right calls with the PDB id in upper case, as the request writes it: the viewer puts molecule_id into PDBe's file address as written, PDBe names its files in lower case, and nothing loads (run in pdbe-molstar 3.3.2 against PDBe on 2026-11-23: 0 structures for '3K34' and '1LMB', 2,387 atoms for '3k34') | 20 | 0 | 20 |
| must fail (wrong) | the same residue number in another chain | 20 | 0 | 0 |
| must fail (wrong) | another palette colour | 20 | 0 | 0 |
| must fail (wrong) | the same calls on another structure | 20 | 0 | 0 |
| must fail (wrong) | another copy of the ligand than the one asked for | 20 | 0 | 0 |
| must fail (wrong) | another representation type for the residue | 20 | 0 | 0 |

## S6. The run manifest

The final run is defined by one manifest file in the repository. Its contents, in words:

- **Corpus.** Version `corpus-v1.0`, SHA-256 `45a841aecbd25a72c0d1f9a91704b3031318955bd44300e3bf547ffa95e4edd8`.
- **Answers.** Each model gives three answers per task and condition (one in the JSON-mode condition);
  no temperature is sent, so each provider's default applies. Limit on the length of an answer:
  8,000 tokens. Models that write reasoning text before the answer, which the
  user does not see, get 16,000 tokens for reasoning and answer
  together, because the provider counts the reasoning against the limit.
- **Retries.** Only transport errors are retried. An invalid answer is archived and scored
  as it stands.
- **Conditions.** 4, as in Section 5.2 of the paper.
- **Budget.** A cap in US dollars; the run refuses to start if the projected cost is above it
  and stops if spending would pass it. Costs are list prices on the day of the run.
- **Validation.** Every parsed scene is validated by Mol\* 5.9.0.

**Table S7. The models.** *Set*: core, or optional (run only if decided so before the run,
from the projected cost; marked † in the paper). Identifiers are given as the provider or
the routing service lists them; the paper uses the part after the slash. *Provider*: the company that publishes the model, as the identifier or the route names it. *Weights*: open if the model's weights can be downloaded, closed if the model can be used only through a provider's service. *Hidden
reasoning*: by default the model first writes reasoning text that the user does not see; the
provider bills it as output and counts it against the limit on the length of the answer. *JSON mode*: the
provider offers an option that forces syntactically valid JSON on the route used. *List
price*: US dollars per million input / output tokens, read on the date given.
⟦PENDING: final run — the version string each provider reports, and the dates of the calls⟧

| Model identifier | Provider | Set | Weights | Hidden reasoning by default | JSON mode | List price, USD per million tokens (input / output) | Price read on |
|:---------|:---|:---|:---|:---|:---|:---|:---|
| Keyword script | – | core | not a model | – | – | 0 / 0 | – |
| Literal script | – | core | not a model | – | – | 0 / 0 | – |
| `claude-haiku-4-5` | anthropic | core | closed | no | no | 1.0 / 5.0 | 2026-11-16 |
| `deepseek/deepseek-v3.2` | deepseek | core | open | no | yes | 0.26 / 0.38 | 2026-11-16 |
| `deepseek/deepseek-v4-flash` | deepseek | core | open | yes | yes | 0.09 / 0.18 | 2026-11-16 |
| `google/gemini-3.5-flash` | google | core | closed | yes | yes | 1.5 / 9.0 | 2026-11-16 |
| `google/gemma-3-27b-it` | google | core | open | no | yes | 0.08 / 0.35 | 2026-11-16 |
| `openai/gpt-5.4-nano` | openai | core | closed | no | yes | 0.2 / 1.25 | 2026-11-16 |
| `meta-llama/llama-4-maverick` | meta-llama | core | open | no | yes | 0.35 / 1.0 | 2026-11-16 |
| `minimax/minimax-m3` | minimax | core | open | yes | yes | 0.3 / 1.2 | 2026-11-16 |
| `mistralai/mistral-small-2603` | mistralai | core | open | no | yes | 0.15 / 0.6 | 2026-11-16 |
| `moonshotai/kimi-k2.6` | moonshotai | core | open | yes | yes | 0.65 / 3.41 | 2026-11-16 |
| `nvidia/nemotron-3-super-120b-a12b` | nvidia | core | open | yes | yes | 0.075 / 0.4 | 2026-11-16 |
| `openai/gpt-oss-120b` | openai | core | open | yes | yes | 0.15 / 0.6 | 2026-11-16 |
| `openai/gpt-oss-20b` | openai | core | open | yes | yes | 0.075 / 0.3 | 2026-11-16 |
| `qwen/qwen3-30b-a3b-instruct-2507` | qwen | core | open | no | yes | 0.1 / 0.3 | 2026-11-16 |
| `qwen/qwen3-next-80b-a3b-instruct` | qwen | core | open | no | yes | 0.09 / 1.1 | 2026-11-16 |
| `z-ai/glm-5.2` | z-ai | core | open | no | yes | 0.007 / 6.8 | 2026-11-16 |
| `anthropic/claude-opus-5.5` | anthropic | optional | closed | yes | yes | 4.0 / 20.0 | 2026-11-16 |
| `openai/gpt-6.1-sol` | openai | optional | closed | yes | yes | 2.0 / 10.0 | 2026-11-16 |
| `google/gemini-4-argon` | google | optional | closed | yes | yes | 2.0 / 10.0 | 2026-11-16 |
| `x-ai/grok-4.7` | x-ai | optional | closed | yes | yes | 2.0 / 6.0 | 2026-11-16 |
| `deepseek/deepseek-v4-pro-0813` | deepseek | optional | open | yes | yes | 0.111 / 4.44 | 2026-11-16 |

### S6.1 Connection test

Before the corpus was frozen, the way from the manifest to a provider and back to a graded
answer was tested once, on a few tasks of the present corpus and with one model of the core
set. We call this the *connection test*. It is not the pilot run of October 2026 (Section
6.6 of the paper), and it is not a result of the benchmark. Every answer of the connection
test that was not counted as a task success was read. This showed faults of the benchmark itself,
which were corrected before the corpus was frozen: among them, wrong answers that had been
graded as right (a file address that does not exist; a PDB identifier in upper case on the
call-list track) and a second representation of the same type that the viewer does not show
(Sections S4.5 and S4.6). No request and no reference changed. The table below gives the
answers as graded after the corrections.

> **CONNECTION TEST.** A test of the connection to one provider on a few tasks, not the benchmark run: these numbers show that the path works, not how good a model is.

**Connection test: claude-haiku-4-5, 39 tasks, 1 sample per task, 46 calls, US $0.21**

| Condition and track | Tasks | Valid answers | Task success rate, strict | Target score, strict | F1, strict | Cost (USD) |
|:---|---:|---:|---:|---:|---:|---:|
| Main, scene track | 21 | 100.0% | 0.667 (14 of 21) | 0.658 | 0.891 | 0.10 |
| Main, call-list track | 18 | 100.0% | 0.333 (6 of 18) | 0.430 | 0.556 | 0.08 |
| Main + grounding pack, scene track | 7 | 85.7% | 0.857 (6 of 7) | 0.857 | 0.857 | 0.03 |

Run of 2026-11-16 on the provider's own service; the archived answers were graded on 2026-11-23 with the grader and corpus as they stood after the faults the test showed were fixed (`PILOT.md` in the repository). The tasks were picked by rule to cover every category, track and kind of task, including the three wordings of one request; they are not a sample of the corpus, and one answer per task says nothing about the spread between answers. *Valid answers*: answers that parse and that the viewer accepts. *Strict*: every answer counts, and an unshowable answer scores 0. The grounding pack states the residue that a variant maps to, so that row is an upper bound.

## S7. System prompts

The two system prompts as sent in the main condition, and then the texts that fill their
slots. A name in double angle brackets, such as `<<MVS_REFERENCE>>`, marks a slot that is
filled with a longer frozen text. These longer texts are the *format guide* of each track:
for the scene track the MolViewSpec reference; for the call-list track the list of actions
with their fields, followed by the reference of the viewer's calls. With its slots filled,
the system prompt has 1,328 words on the scene track and
1,556 on the call-list track. In the condition without a format guide, the
section "MVS reference" is removed. Each prompt has one worked example, on entry 1HSG, which
no task uses: the example of the call-list prompt is in the prompt itself, and that of the
scene prompt sits inside its format guide. The format guide of the scene track also has one
short illustration of a distance line on entry 1A6M, which tasks use; no task asks for that
distance.

The prompts and guides are printed as sent, each line indented by two spaces so that their own
headings are not read as headings of this document. They use the words of the repository and
not those of the paper; Table S0c lists the names that differ.

**Scene track: system prompt.**

````text
  You are a molecular-visualization agent. The user gives a natural-language
  instruction; you translate it into a **MolViewSpec (MVS) scene tree**.

  You do NOT write Python. You output a single JSON object: the MVS state, of the
  form `{"root": {"kind": "root", "children": [ ... ]}}`.

  ## Output contract

  * Output **only** the JSON object. No prose, no markdown fences, no explanation.
  * Build the scene by nesting nodes: `download` → `parse` → `structure` →
    `component` → `representation` → `color` (add `focus`/`label` as needed).
  * Use real PDB IDs in the download URL: `https://files.rcsb.org/download/<id>.cif`
    with `parse` format `mmcif`.
  * Select specific residues with a ComponentExpression
    (`{"auth_asym_id": "A", "auth_seq_id": 35}`); use real chain ids and residue
    numbers. Make your best specific guess rather than a vague selection.
  * Only include what the user asks for — MVS is additive, so to "hide waters" you
    simply do not add a water component.
  * The answer is judged by what the viewer ends up showing: which atoms are drawn, in
    which representation and colour, plus labels, focus and measurements. How the tree
    is written does not matter; anything drawn that was not asked for counts against it.

  ## Follow-up requests

  Sometimes the request comes with the current scene (an MVS state). Then output the
  **complete** new scene: the current scene with the requested change made and
  everything else kept as it is. If the request needs no change, output the current
  scene unchanged.

  ## MVS reference

  <<MVS_REFERENCE>>
````

**Call-list track: system prompt.**

````text
  You are a molecular-visualization agent. The user gives a natural-language
  request; you translate it into a sequence of calls to PDBe's Mol* viewer
  (pdbe-molstar 3.3.2, hosted here by `ipymolstar.PDBeMolstar`).

  You do NOT write Python. Instead you emit a JSON array of **canonical actions**
  (an intermediate representation that maps 1:1 onto the viewer's API). Each element
  is an object with an `"action"` field plus that action's parameters.

  ## Output contract

  * Output **only** the JSON array. No prose, no markdown fences, no explanation.
  * Order matters: emit actions in the order they should execute.
  * Use real PDB IDs and real residue numbers/chains. Selections use the
    `QueryParam` keys documented below (`auth_asym_id`, `auth_seq_id`,
    `label_comp_id`, `atoms`, ...).
  * The answer is judged by the state the viewer ends in: what is loaded, which atoms
    are drawn and how, their colours, the camera focus, tooltips and settings.
  * If you are unsure of an exact residue number, still make your best specific
    guess — vague answers score poorly.

  ## Follow-up requests

  Sometimes the request comes with the calls already made in this viewer session. Then
  output the **complete** call list for the new state, as if starting from an empty
  viewer: the earlier calls that still apply, followed by any new ones. If the request
  needs no change, output the earlier calls unchanged.

  ## Canonical actions

  <<SCHEMA_TEXT>>

  ## Target API reference

  <<API_REFERENCE>>

  ## Worked example

  User: "Load HIV-1 protease bound to indinavir (1HSG), hide the waters, colour the
  catalytic Asp25 of chains A and B red, and centre the view on the inhibitor."

  Output:
  ```json
  [
    {"action": "load", "molecule_id": "1hsg"},
    {"action": "set_property", "name": "hide_water", "value": true},
    {"action": "color", "data": [
      {"auth_asym_id": "A", "auth_seq_id": 25, "color": "red"},
      {"auth_asym_id": "B", "auth_seq_id": 25, "color": "red"}]},
    {"action": "focus", "data": [{"label_comp_id": "MK1"}]}
  ]
  ```
  (Emit the array only — the fences above are illustrative.)
````

**Scene track: the format guide** (slot `<<MVS_REFERENCE>>`), 1,087 words.

`````text
  # MolViewSpec (MVS) — scene-tree reference (vendored)

  > **Frozen snapshot** of the MVS scene tree as implemented by Mol\* 5.9.0 (the
  > version vendored in `molbench/static/molstar/`). This is both the context the
  > model-under-test receives (the **Spec** condition) and the structure the grader
  > trusts. It covers the structure-scene subset of MVS; volumes, trajectories,
  > annotation files (`*_from_uri`/`*_from_source`) and multi-snapshot animation are
  > left out.

  MVS describes a 3D molecular scene as a **tree of nodes**. A scene is built by
  nesting: you download data, parse it, derive a structure, carve out components,
  and give each a representation and colour.

  ## State shape

  ```json
  {
    "root": {
      "kind": "root",
      "children": [ <node>, ... ]
    }
  }
  ```

  Every node is `{"kind": <str>, "params": {<...>}, "children": [<node>, ...]}`
  (`params`/`children` omitted when empty). Nesting encodes meaning — a `color` node
  is a child of the `representation` it colours, which is a child of the `component`
  it draws. A node may also carry `"custom": {...}`: viewer-specific extras (see
  *Mol\* extensions* below).

  ## Node kinds

  | kind | params | parent | meaning |
  |---|---|---|---|
  | `download` | `url` | root | fetch a structure file |
  | `parse` | `format` (`mmcif`,`bcif`,`pdb`) | download | parse the data |
  | `structure` | `type` (`model`,`assembly`,`symmetry`), `assembly_id`, `model_index` | parse | build a structure |
  | `transform` | `rotation` (3×3, flat), `translation`, or `matrix` (4×4, flat) | structure | move it by a known matrix |
  | `component` | `selector` | structure | select a subset to draw |
  | `representation` | `type`, `size_factor` | component | how to draw it |
  | `color` | `color`, optional `selector` | representation | colour it (or only the selected part) |
  | `opacity` | `opacity` (0–1; 0.5 = 50% transparent) | representation | transparency |
  | `label` | `text` | component | text label on the component |
  | `tooltip` | `text` | component | hover text |
  | `focus` | optional `radius` | component (or root) | aim the camera at it |
  | `camera` | `target`, `position`, `up` | root | set the camera explicitly |
  | `canvas` | `background_color` | root | background colour |
  | `primitives` | optional `color`, `label_color`, `opacity` | structure | a group of drawn shapes |
  | `primitive` | `kind` + params below | primitives | one shape |

  **Structure files** (`download`): a PDB entry is
  `https://files.rcsb.org/download/<id>.cif`, parsed as `mmcif`. An AlphaFold DB model
  is `https://alphafold.ebi.ac.uk/files/AF-<accession>-F1-model_v6.cif`, parsed as
  `mmcif`; AlphaFold DB serves the model under no other name, and RCSB does not hold it.

  **Component selectors** — a string for whole classes:
  `all`, `polymer`, `protein`, `nucleic`, `ligand`, `ion`, `water`, `branched`.
  Or a **ComponentExpression** object (or list of them) to pick specific atoms/residues:

  | field | meaning |
  |---|---|
  | `auth_asym_id` | author chain id (e.g. `"A"`) |
  | `auth_seq_id` | author residue number |
  | `label_asym_id`, `label_seq_id` | label (mmCIF) chain / residue |
  | `beg_auth_seq_id`, `end_auth_seq_id` | inclusive residue range (also `beg_/end_label_seq_id`) |
  | `label_comp_id`, `auth_comp_id` | residue/ligand 3-letter code (`"HEM"`) |
  | `label_atom_id`, `auth_atom_id` | atom name (`"FE"`, `"NE2"`) |
  | `type_symbol` | element (`"FE"`) |
  | `residue_index` | 0-based residue index in the file |

  Fields in one expression are AND-ed; a list of expressions is OR-ed. A selection
  that matches nothing draws nothing — it is not an error, so use real chain ids,
  residue numbers and atom names.

  **Representation types:** `cartoon`, `backbone`, `ball_and_stick`, `line`,
  `spacefill`, `surface`, `putty`, `carbohydrate`.

  **Colours:** lowercase CSS names (`"red"`, `"orange"`, `"steelblue"`) or hex
  (`"#FF6699"`). A `color` node takes ONE colour. To colour part of a representation,
  give it a second `color` child with a `selector`; later `color` children paint over
  earlier ones.

  **Two representations of the same type on the same atoms coincide.** Only the one
  listed first is seen (a grey cartoon of the polymer followed by a green cartoon of
  residues 10-20 shows a cartoon that is grey all over). Representations of different
  types on the same atoms (a cartoon and ball-and-stick) are both seen.

  ## Worked example

  Prompt: *"Load 1HSG; protein as grey cartoon, the inhibitor MK1 as orange ball-and-stick."*

  ```json
  {"root": {"kind": "root", "children": [
    {"kind": "download", "params": {"url": "https://files.rcsb.org/download/1hsg.cif"},
     "children": [
      {"kind": "parse", "params": {"format": "mmcif"}, "children": [
       {"kind": "structure", "params": {"type": "model"}, "children": [
         {"kind": "component", "params": {"selector": "polymer"}, "children": [
           {"kind": "representation", "params": {"type": "cartoon"}, "children": [
             {"kind": "color", "params": {"color": "gray"}}]}]},
         {"kind": "component", "params": {"selector": {"label_comp_id": "MK1"}}, "children": [
           {"kind": "representation", "params": {"type": "ball_and_stick"}, "children": [
             {"kind": "color", "params": {"color": "orange"}}]}]}
       ]}]}]}
  ]}}
  ```

  A named compound is selected by its code, as above: the string `"ligand"` is every
  ligand of the entry at once. To select specific residues, use an expression such as
  `"selector": {"auth_asym_id": "A", "auth_seq_id": 35}`.

  **Transparency:** `{"kind": "opacity", "params": {"opacity": 0.5}}` as a child of
  the `representation`, beside its `color`.

  ## Primitives: lines, distances, angles, 3D text

  A primitive position (`start`, `end`, `position`, `a`/`b`/`c`) is either
  `[x, y, z]` or a ComponentExpression naming **one atom**, e.g.
  `{"auth_asym_id": "A", "auth_seq_id": 64, "label_atom_id": "NE2"}`
  (if it matches several atoms, their centre is used).

  | primitive `kind` | params | draws |
  |---|---|---|
  | `distance_measurement` | `start`, `end`, `color`, `radius`, `dash_length`, `label_template` | a dashed line labelled with its length (`"{​{distance}}"` is replaced by it) |
  | `tube` | `start`, `end`, `radius`, `dash_length` | a line, dashed if `dash_length` is set |
  | `angle_measurement` | `a`, `b`, `c` | the angle at `b`, labelled |
  | `arrow` | `start`, `end`, `tube_radius`, `color` | an arrow |
  | `label` | `position`, `text`, `label_size` | 3D text |

  Example — *"1A6M: show the distance from the distal His64 to the bound O2"*
  (the ligand code is `OXY`). The `primitives` node is a child of `structure`, next
  to its `component` nodes:

  ```json
  {"kind": "primitives", "params": {"color": "yellow", "label_color": "yellow"}, "children": [
    {"kind": "primitive", "params": {"kind": "distance_measurement",
      "start": {"auth_asym_id": "A", "auth_seq_id": 64, "label_atom_id": "NE2"},
      "end": {"auth_asym_id": "A", "label_comp_id": "OXY", "label_atom_id": "O2"},
      "radius": 0.06, "dash_length": 0.15, "label_template": "{​{distance}}"}}]}
  ```

  ## Mol\* extensions (`custom`)

  Mol\* reads these `custom` keys; other MVS viewers ignore them.

  * **Non-covalent interactions** (H-bonds, salt bridges, metal coordination, π
    stacking…), computed by Mol\*: on a `component`, set
    `"custom": {"molstar_show_non_covalent_interactions": true,
    "molstar_non_covalent_interactions_radius_ang": 5}`. Mol\* draws the residues
    within the radius as ball-and-stick plus dashed interaction lines coloured by
    type. The component needs no `representation` child for this.
  * **Colour schemes** (rainbow, by chain, by secondary structure, by element): give
    the representation ONE `color` child carrying
    `"custom": {"molstar_color_theme_name": <theme>}` (its `color` param is a
    placeholder the theme overrides). Themes: `"sequence-id"`, `"chain-id"`,
    `"secondary-structure"`, `"element-symbol"`.
`````

**Call-list track: the format guide, first part (the list of actions)** (slot `<<SCHEMA_TEXT>>`), 228 words.

`````text
  Each action is an object {"action": <name>, ...fields}. Fields marked * are required.
  - load(molecule_id, custom_data, assembly_id, preset, ligand_view, alphafold): Load a structure into the viewer.
  - set_visual_style(style*): Set the global representation for the whole structure.
  - set_property(name*, value*): Toggle/assign a widget property (e.g. hide_water, spin, bg_color).
  - color(data*, non_selected_color, keep_colors, keep_representations): Colour/select a set of residues (PDBeMolstar.color).
  - focus(data*): Centre and zoom the camera on a selection (PDBeMolstar.focus).
  - highlight(data*, color, focus): Transiently highlight a selection (PDBeMolstar.highlight).
  - tooltips(data*): Attach tooltips to a selection (PDBeMolstar.tooltips).
  - set_color(highlight, select): Set the highlight and/or select colours (PDBeMolstar.set_color).
  - reset(camera, theme, highlightColor, selectColor): Reset camera/theme/colours (PDBeMolstar.reset).
  - clear_highlight(): Clear current highlight.
  - clear_selection(): Clear current selection.
  - clear_tooltips(): Clear current tooltips.
  set_visual_style.style and a selection's representation: cartoon | ball-and-stick | carbohydrate | ellipsoid | gaussian-surface | molecular-surface | point | putty | spacefill
  load.preset: default | unitcell | all-models | supercell
  set_property.name: hide_polymer (bool), hide_water (bool), hide_heteroatoms (bool), hide_carbs (bool), hide_non_standard (bool), hide_coarse (bool), spin (bool), superposition (bool), superposition_params (dict), load_maps (bool), map_settings (dict), validation_annotation (bool), domain_annotation (bool), symmetry_annotation (bool), alphafold_view (bool), sequence_panel (bool), bg_color (str), highlight_color (str), select_color (str), lighting (str)
  data is a list of selections (QueryParam objects). Locator keys: entity_id, struct_asym_id, auth_asym_id, label_comp_id, residue_number, start_residue_number, end_residue_number, auth_seq_id, auth_residue_number, auth_ins_code_id, start_auth_residue_number, end_auth_residue_number, start_auth_ins_code_id, end_auth_ins_code_id, uniprot_accession, uniprot_residue_number, start_uniprot_residue_number, end_uniprot_residue_number, atoms, atom_id. Styling keys: color, representation, representationColor, sideChain, focus, tooltip.
`````

**Call-list track: the format guide, second part (the reference of the viewer's calls)** (slot `<<API_REFERENCE>>`), 1,025 words.

`````text
  # ipymolstar `PDBeMolstar` — API reference (vendored)

  > **Frozen snapshot** of the public surface of `ipymolstar.PDBeMolstar` **0.1.0**, which
  > drives PDBe's Mol* viewer, **pdbe-molstar 3.3.2**. Behaviour notes below were read from
  > that release's source and checked in the running viewer. This file is the *authority*
  > for the benchmark: it is the context shown to the model-under-test and the spec the
  > grader follows. Do not edit to "fix" a model's mistake — pin a new snapshot instead.

  You configure the viewer by setting **traits** and trigger one-shot operations by
  calling **methods**.

  ## Traits

  | Trait | Type | Notes |
  |---|---|---|
  | `molecule_id` | str | PDB id in **lower case**, e.g. `"1cbs"`: the viewer puts it into the file address as written, and `"1CBS"` loads nothing. With `superposition=True` it is a **UniProt accession** instead. |
  | `custom_data` | dict | `{"url": str, "format": "cif"\|"bcif"\|"pdb", "binary": bool}` — load any structure file by URL instead of a PDB id. An AlphaFold DB model is `https://alphafold.ebi.ac.uk/files/AF-<accession>-F1-model_v6.cif`. |
  | `assembly_id` | str | Biological assembly to build, e.g. `"1"`; `"preferred"` = the first. Default: the deposited model. |
  | `default_preset` | enum | `default` \| `unitcell` \| `all-models` \| `supercell`. |
  | `ligand_view` | dict | PDBe ligand page view: only that ligand and its surroundings. `{"label_comp_id": "REA"}` and/or `auth_asym_id` + `auth_seq_id`. |
  | `alphafold_view` | bool | Colour by AlphaFold confidence (pLDDT). It does **not** load a model: load one with `custom_data`. |
  | `superposition` | bool | PDBe-KB superposition view: the superposed PDB entries of one protein, addressed by UniProt accession in `molecule_id`. |
  | `superposition_params` | dict | `{"matrixAccession": str, "segment": int, "cluster": [int], "superposeCompleteCluster": bool, "ligandView": bool, "superposeAll": bool, "ligandColor": color}`. |
  | `visual_style` | enum | One representation for every component: `cartoon`, `ball-and-stick`, `carbohydrate`, `ellipsoid`, `gaussian-surface`, `molecular-surface`, `point`, `putty`, `spacefill`. Unset = the default view: polymer as cartoon; ligands, ions, waters and non-standard residues as ball-and-stick. `cartoon` and `putty` draw polymer only (ligands, ions and waters disappear). |
  | `hide_polymer`, `hide_water`, `hide_heteroatoms`, `hide_carbs`, `hide_non_standard`, `hide_coarse` | bool | Hide the polymer / waters / ligands and ions / carbohydrates / non-standard residues / coarse parts. They switch off the viewer's own drawing of that component; a representation added by `color()` (below) is not part of it and stays on screen. |
  | `load_maps` | bool | Load electron-density (or EM) maps. |
  | `map_settings` | dict | Map style, e.g. `{"2fo-fc": {"opacity": 0.5, "wireframe": True}}` (also `"fo-fc(+ve)"`, `"fo-fc(-ve)"`, `"em"`). |
  | `validation_annotation`, `domain_annotation`, `symmetry_annotation` | bool | PDBe validation / domain / assembly-symmetry overlays. |
  | `bg_color` | str | Background, a CSS colour, e.g. `"#FFFFFF"`. |
  | `highlight_color`, `select_color` | str | Hover-highlight and selection-mode colours (`"#rrggbb"` or a colour name). |
  | `lighting` | enum | `flat` \| `matte` \| `glossy` \| `metallic` \| `plastic`. |
  | `spin` | bool | Spin the camera. |
  | `sequence_panel` | bool | Show the sequence panel. |

  Setting `molecule_id`, `custom_data` or `visual_style` **reloads the structure**: colouring,
  added representations and the camera focus made before it are lost. Set them first.

  ## Methods

  ```python
  def color(data: list[QueryParam], non_selected_color=None,
            keep_colors=False, keep_representations=False) -> None
  ```
  pdbe-molstar's `select`. For each item of `data`:

  * `color` paints the selected atoms in the representations the structure **already has**
    (not in ones this call adds). Left out, they are painted the default orange
    (255,112,3); `"color": None` leaves them as they are.
  * `representation` (or `sideChain=True`, meaning ball-and-stick) **adds** a representation
    for the selected residues, in element or chain colours unless `representationColor` is
    given.
  * `focus=True` also zooms on the item.

  `non_selected_color` paints everything else. Each call first **removes** the colouring and
  the added representations of earlier calls, unless `keep_colors` / `keep_representations`.

  ```python
  def focus(data: list[QueryParam]) -> None    # centre and zoom the camera on the selection
  highlight = {"data": [...], "color": ..., "focus": bool}   # (trait) hover-style highlight; color and focus optional
  tooltips = {"data": [{..., "tooltip": "text"}]}            # (trait) replaces earlier tooltips
  def set_color(highlight=None, select=None) -> None         # same as the highlight_color / select_color traits
  def reset(data) -> None     # keys: camera, theme, highlightColor, selectColor (bool)
  def clear_highlight() -> None
  def clear_selection() -> None                # removes colouring and added representations
  def clear_tooltips() -> None
  ```

  ## `QueryParam` — the selection language

  A dict; its tests are AND-ed, a list of dicts is the union. `{}` selects everything.

  | Key | Meaning |
  |---|---|
  | `entity_id` | mmCIF entity id (str, e.g. `"1"`) |
  | `struct_asym_id` | **label** chain id (mmCIF `label_asym_id`); wins if both chain keys are given |
  | `auth_asym_id` | **author** chain id — the chain letter in the paper and the PDB file |
  | `label_comp_id` | residue/ligand code, e.g. `"HEM"`, `"HOH"` (upper case). **Overrides** every residue-number key |
  | `residue_number` | **label** residue number (mmCIF `label_seq_id`: 1-based position in the deposited sequence) |
  | `start_residue_number`, `end_residue_number` | inclusive **label** range |
  | `auth_seq_id` (alias `auth_residue_number`) | **author** residue number — the number used in the literature (His57, Asp25) |
  | `start_auth_residue_number`, `end_auth_residue_number` | inclusive **author** range |
  | `auth_ins_code_id` | accepted but **ignored** by this viewer release: an insertion code cannot be selected. `auth_seq_id: 221` selects 221 and 221A alike; name one of them by `struct_asym_id` + `residue_number` |
  | `uniprot_accession` + `uniprot_residue_number` | residue by UniProt numbering (the viewer maps it with SIFTS) |
  | `uniprot_accession` + `start_uniprot_residue_number`, `end_uniprot_residue_number` | UniProt range |
  | `atoms` | list of atom names, e.g. `["CA", "CB"]` |
  | `color`, `representation`, `representationColor`, `sideChain`, `focus` | see `color()` |
  | `tooltip` | str — text for `tooltips` |

  Label and author numbers often differ; a residue named the way papers name it needs the
  **author** keys. Numbers are ints, not strings. Colours are `{"r": int, "g": int, "b": int}`,
  `"#rrggbb"`, or a lower-case CSS colour name (`"red"`, `"orange"`).

  Example — HIV-1 protease 1HSG: colour the catalytic Asp25 of both chains red and add red
  ball-and-stick for them, leave the rest white, then centre on the inhibitor (MK1):

  ```python
  view.color(
      data=[
          {"auth_asym_id": "A", "auth_seq_id": 25, "color": "red",
           "representation": "ball-and-stick", "representationColor": "red"},
          {"auth_asym_id": "B", "auth_seq_id": 25, "color": "red",
           "representation": "ball-and-stick", "representationColor": "red"},
      ],
      non_selected_color="white",
  )
  view.focus(data=[{"label_comp_id": "MK1"}])
  ```
`````

A single-turn request is sent as the user message. A follow-up task is sent as the current
scene (scene track) or the calls made so far (call-list track), followed by `Request: …`.

## S8. Further tables of the pilot run (October 2026)

**These tables are preliminary.** They were written by script from the archived pilot run and
are the record behind Section 6.6 of the paper. They differ from Section 6.6 in one way that
matters: the scores here are those of the *earlier* scene grader, which compared scene trees
path by path, whereas Section 6.6 regrades the same answers on drawn state. Its numbers
therefore differ, and not all in one direction. F1 is lower there, most of all in the clinical
category (0.31 against 0.48 here).
The share of exactly right answers is in places higher: in the translation category the task
success rate of Section 6.6 is 69.9%, and the share of answers
with a score of 1 here is 65.4%. Three column names differ from those of the paper, so that no word has two
meanings. *Score of 1* is the share of answers that score exactly 1 under the earlier grader
(the forerunner of task success). *Earlier-grader F1* is the F1 of that grader. *Requested
part*, in Table S14, is defined in the caption of that table; the pilot tasks stored no
target, so there is no target score in these tables.

Two notes on single tables. In Table S10 the caption defines five classes and the table has
four columns: no answer of the pilot run fell in the class "JSON, not a scene". In Table S14
the count for the clinical category (85 answers with
the requested part exactly right) differs slightly from that of Section 6.6 of the paper
(87), because the two are found by different rules: here
by the earlier grader, component by component of the scene tree, and there on drawn state.

**Table S8. Corpus of the October 2026 pilot run (preliminary, earlier grader).** Tasks and distinct structures (PDB entries) per category. The categories are those of the first-version corpus.

| Category | Tasks | Structures |
| :--- | ---: | ---: |
| Translation | 41 | 7 |
| Structure-grounded | 8 | 6 |
| Clinical | 9 | 1 |
| Name resolution | 6 | 6 |
| Interactions | 6 | 3 |
| **All** | 70 | 14 |

**Table S9. Scene track, main condition (pilot run, preliminary, earlier grader).** 15 models, 70 tasks on 14 structures, 1 answer per task. *Strict F1*: mean score over all tasks, where an answer the viewer cannot show scores 0. *Valid*: share of answers that parse as JSON and that Mol\* accepts and loads. *F1 (valid)*: mean score over the valid answers only. *Score of 1*: share of answers that are valid and score exactly 1. 95% interval: bootstrap over tasks, resampling whole structures (10000 replicates). Weights: open if the weights of the model can be downloaded.

| # | Model | Weights | Strict F1 | 95% interval | Valid | 95% interval | F1 (valid) | 95% interval | Score of 1 |
| ---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | deepseek-v3.2 | open | 0.903 | 0.829–0.958 | 98.6% | 95.8%–100.0% | 0.916 | 0.839–0.965 | 64.3% |
| 2 | deepseek-v4-flash | open | 0.859 | 0.768–0.928 | 92.9% | 87.5%–97.3% | 0.925 | 0.824–0.983 | 62.9% |
| 3 | claude-haiku-4-5 | closed | 0.857 | 0.731–0.929 | 95.7% | 86.8%–100.0% | 0.895 | 0.799–0.954 | 60.0% |
| 4 | gemini-3.5-flash | closed | 0.849 | 0.712–0.938 | 94.3% | 85.5%–100.0% | 0.900 | 0.790–0.963 | 70.0% |
| 5 | minimax-m3 | open | 0.817 | 0.692–0.891 | 90.0% | 82.2%–94.9% | 0.907 | 0.817–0.959 | 60.0% |
| 6 | qwen3-next-80b-a3b-instruct | open | 0.805 | 0.702–0.899 | 91.4% | 83.1%–100.0% | 0.881 | 0.794–0.931 | 45.7% |
| 7 | glm-5.2 | open | 0.805 | 0.713–0.867 | 90.0% | 82.8%–95.5% | 0.895 | 0.797–0.956 | 57.1% |
| 8 | llama-4-maverick | open | 0.792 | 0.604–0.915 | 81.4% | 63.8%–92.9% | 0.973 | 0.938–0.992 | 70.0% |
| 9 | gemma-3-27b-it | open | 0.713 | 0.596–0.814 | 81.4% | 69.9%–92.1% | 0.876 | 0.761–0.946 | 48.6% |
| 10 | kimi-k2.6 | open | 0.657 | 0.523–0.760 | 72.9% | 60.0%–82.8% | 0.902 | 0.799–0.973 | 47.1% |
| 11 | gpt-5.4-nano | closed | 0.654 | 0.511–0.749 | 75.7% | 63.6%–84.3% | 0.864 | 0.778–0.915 | 15.7% |
| 12 | gpt-oss-120b | open | 0.561 | 0.422–0.657 | 62.9% | 51.8%–71.7% | 0.893 | 0.785–0.948 | 35.7% |
| 13 | qwen3-30b-a3b-instruct-2507 | open | 0.519 | 0.332–0.665 | 55.7% | 37.9%–70.2% | 0.932 | 0.856–0.969 | 37.1% |
| 14 | gpt-oss-20b | open | 0.252 | 0.165–0.333 | 28.6% | 19.7%–37.0% | 0.883 | 0.726–0.981 | 20.0% |
| 15 | nemotron-3-super-120b-a12b | open | 0.078 | 0.027–0.130 | 8.6% | 3.3%–13.8% | 0.910 | 0.700–1.000 | 5.7% |

**Table S10. What happened to each answer, main condition (pilot run, preliminary, earlier grader).** Every answer falls into exactly one class. *Valid scene*: parses as JSON, Mol\* accepts it as MolViewSpec and loads the structure. *Invalid JSON*: no parsable JSON object. *JSON, not a scene*: valid JSON that is not a MolViewSpec tree. *Scene rejected by Mol\**: a tree with a wrong node or parameter. *Structure failed to load*: the scene is well formed but names a file that does not load. All classes except the first score 0.

| Model | valid scene | invalid JSON | scene rejected by Mol* | structure failed to load |
| :--- | ---: | ---: | ---: | ---: |
| deepseek-v3.2 | 69 | 0 | 0 | 1 |
| claude-haiku-4-5 | 67 | 0 | 3 | 0 |
| gemini-3.5-flash | 66 | 4 | 0 | 0 |
| deepseek-v4-flash | 65 | 4 | 1 | 0 |
| qwen3-next-80b-a3b-instruct | 64 | 3 | 3 | 0 |
| minimax-m3 | 63 | 5 | 2 | 0 |
| glm-5.2 | 63 | 5 | 1 | 1 |
| gemma-3-27b-it | 57 | 4 | 9 | 0 |
| llama-4-maverick | 57 | 1 | 11 | 1 |
| gpt-5.4-nano | 53 | 15 | 2 | 0 |
| kimi-k2.6 | 51 | 18 | 1 | 0 |
| gpt-oss-120b | 44 | 26 | 0 | 0 |
| qwen3-30b-a3b-instruct-2507 | 39 | 28 | 3 | 0 |
| gpt-oss-20b | 20 | 50 | 0 | 0 |
| nemotron-3-super-120b-a12b | 6 | 64 | 0 | 0 |
| **All models** | 784 | 227 | 36 | 3 |

**Table S11. Shape of the invalid-JSON answers (pilot run, preliminary, earlier grader).** For the 199 invalid-JSON answers whose raw text was archived: does the text open and close the same number of braces? A scene is a deeply nested tree, so a miscount by one brace is enough to lose the whole answer.

| Shape | Answers | Share |
| :--- | ---: | ---: |
| too many closing braces | 72 | 36.2% |
| too few closing braces | 59 | 29.6% |
| braces balance; other syntax error | 53 | 26.6% |
| empty answer | 15 | 7.5% |

**Table S12. Offline JSON-repair counterfactual, main condition (pilot run, preliminary, earlier grader).** Each invalid-JSON answer with archived raw text was passed through the `json-repair` library and graded again. No model was called. *Strict F1* is the reported score. *Repaired F1* adds the score of the repaired answers. The repaired scenes were graded as trees but **not** checked by Mol\*, so repaired F1 is an upper bound. Answers with no archived raw text stay at 0 (*Raw text* < *Invalid JSON*).

| Model | Invalid JSON | Raw text | Repaired to a scene | Strict F1 | Repaired F1 | Change |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| deepseek-v3.2 | 0 | 0 | 0 | 0.903 | 0.903 | +0.000 |
| deepseek-v4-flash | 4 | 4 | 4 | 0.859 | 0.913 | +0.054 |
| claude-haiku-4-5 | 0 | 0 | 0 | 0.857 | 0.857 | +0.000 |
| gemini-3.5-flash | 4 | 4 | 3 | 0.849 | 0.866 | +0.018 |
| minimax-m3 | 5 | 5 | 4 | 0.817 | 0.862 | +0.045 |
| qwen3-next-80b-a3b-instruct | 3 | 3 | 3 | 0.805 | 0.848 | +0.043 |
| glm-5.2 | 5 | 5 | 5 | 0.805 | 0.869 | +0.064 |
| llama-4-maverick | 1 | 1 | 1 | 0.792 | 0.797 | +0.005 |
| gemma-3-27b-it | 4 | 4 | 4 | 0.713 | 0.757 | +0.044 |
| kimi-k2.6 | 18 | 18 | 7 | 0.657 | 0.754 | +0.097 |
| gpt-5.4-nano | 15 | 15 | 15 | 0.654 | 0.798 | +0.144 |
| gpt-oss-120b | 26 | 26 | 26 | 0.561 | 0.874 | +0.313 |
| qwen3-30b-a3b-instruct-2507 | 28 | 0 | 0 | 0.519 | 0.519 | +0.000 |
| gpt-oss-20b | 50 | 50 | 47 | 0.252 | 0.868 | +0.616 |
| nemotron-3-super-120b-a12b | 64 | 64 | 64 | 0.078 | 0.911 | +0.833 |

**Table S13. Scores by category, main condition (pilot run, preliminary, earlier grader).** *Valid / all*: valid answers out of all answers, pooled over models. *Models*: models with at least one valid answer in the category (the others cannot contribute to a valid-only mean). *F1 (valid)*: mean score over valid answers, first averaged per model and then over models (mean), and over all valid answers together (pooled). *Strict F1*: mean over all answers, invalid ones scoring 0, averaged per model then over models. *Score of 1*: share of answers that are valid and score exactly 1. 95% intervals are for the pooled valid-only and pooled strict values, resampling whole structures; n/a where a category has a single structure. Rows with few tasks must be read with care: the numbers of tasks are in the table.

| Category | Tasks | Structures | Valid / all | Models | F1 (valid), mean | F1 (valid), pooled | 95% interval | Strict F1 | 95% interval | Score of 1 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Translation | 41 | 7 | 491/615 | 15/15 | 0.978 | 0.977 | 0.974–0.979 | 0.780 | 0.755–0.795 | 65.4% |
| Structure-grounded | 8 | 6 | 91/120 | 14/15 | 0.972 | 0.971 | 0.955–0.991 | 0.737 | 0.705–0.770 | 53.3% |
| Clinical | 9 | 1 | 96/135 | 15/15 | 0.672 | 0.679 | n/a | 0.483 | n/a | 1.5% |
| Name resolution | 6 | 6 | 52/90 | 12/15 | 0.542 | 0.564 | 0.512–0.606 | 0.326 | 0.247–0.392 | 2.2% |
| Interactions | 6 | 3 | 54/90 | 14/15 | 0.850 | 0.854 | 0.822–0.884 | 0.512 | 0.356–0.770 | 22.2% |

**Table S14. Is the requested component itself right? main condition (pilot run, preliminary, earlier grader).** Valid scenes only. The *requested part* of a task is every component of the reference scene except, when the reference has more than one, the component with the most atoms, which is treated as *context* (for example a grey cartoon of the whole protein behind one highlighted residue). *Requested part exact*: the answer draws every requested part with exactly the reference atoms, representation and colour. *Scene exact*: the whole scene scores 1. *Requested part exact, scene not*: the requested part is right and the scene still loses points for something else (missing or different context, extra components). *Atoms only*: the atoms of the requested part are selected exactly, in the reference entry or an accepted one, but drawn or coloured differently. *Requested part wrong*: no component selects exactly the atoms of the requested part.

| Category | Valid scenes | Requested part exact | Share | Scene exact | Requested part exact, scene not | Atoms only | Requested part wrong |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Translation | 491 | 404 | 82.3% | 402 | 2 | 55 | 32 |
| Structure-grounded | 91 | 64 | 70.3% | 64 | 0 | 2 | 25 |
| Clinical | 96 | 85 | 88.5% | 2 | 83 | 2 | 9 |
| Name resolution | 52 | 2 | 3.9% | 2 | 0 | 33 | 17 |
| Interactions | 54 | 22 | 40.7% | 20 | 2 | 15 | 17 |

**Table S15. Where valid scenes lose points, main condition (pilot run, preliminary, earlier grader).** For the 294 valid scenes that scored below 1 (of 784 valid scenes): which part of the scene differs from the reference. One scene can differ in several parts, so the rows add up to more than the total. *Selection*: the right kind of component, but it picks different atoms. *Unrequested colour*: the answer colours something the reference leaves at the viewer default; the earlier-grader F1 counts this as a difference even where a reader might not. *Missing* / *extra component*: a part of the reference scene is absent, or the answer draws something the reference does not. *Structure*: a different entry or file is loaded.

| Difference | Scenes | Share | Translation | Structure-grounded | Clinical | Name resolution | Interactions |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| selection | 126 | 42.9% | 60 | 25 | 21 | 3 | 17 |
| unrequested colour | 73 | 24.8% | 0 | 0 | 0 | 50 | 23 |
| missing component | 68 | 23.1% | 2 | 0 | 66 | 0 | 0 |
| extra component | 65 | 22.1% | 1 | 1 | 17 | 26 | 20 |
| wrong colour | 64 | 21.8% | 51 | 0 | 13 | 0 | 0 |
| structure | 44 | 15.0% | 19 | 5 | 2 | 16 | 2 |
| camera | 13 | 4.4% | 9 | 0 | 0 | 0 | 4 |
| representation | 12 | 4.1% | 3 | 0 | 8 | 0 | 1 |
| drawn lines or labels | 12 | 4.1% | 0 | 0 | 0 | 0 | 12 |
| missing colour | 10 | 3.4% | 0 | 0 | 10 | 0 | 0 |
| *imperfect valid scenes* | 294 |  | 89 | 27 | 94 | 50 | 34 |

**Table S16. Effect of grounding packs (pilot run, preliminary, earlier grader).** Change in F1 when the task's frozen grounding pack is added to the request (main + grounding pack minus main), for the 15 models that ran both. Three ways to count, because they answer different questions. Row 1 includes the answers that became invalid. Row 2 keeps only the 15 tasks that need a lookup (Clinical, Name resolution). Row 3 keeps only task-model combinations whose answer was valid in both conditions, so it isolates the effect on content; of those combinations 69 improved, 92 got worse and 486 did not change. 95% interval: bootstrap, resampling whole structures.

| Comparison | n | Change in F1 | 95% interval |
| :--- | ---: | ---: | ---: |
| All tasks, all answers (mean over models) | 70 | -0.041 | -0.066 to -0.021 |
| Lookup tasks only, all answers (mean over models) | 15 | -0.021 | -0.038 to +0.006 |
| Task-model combinations valid in both conditions (pooled) | 647 | -0.004 | -0.010 to +0.003 |

**Table S17. Prompting conditions (pilot run, preliminary, earlier grader).** main: the system prompt contains the format guide. no format guide: it contains only the rule for the answer ("answer with one MolViewSpec JSON scene"). + grounding pack: the task's frozen grounding pack (facts about the structure, built offline) is added to the request. Each row is a mean over the models that ran that condition; the number of models differs by row and is stated. *Strict F1*, *Valid* and *F1 (valid)* as in the per-model table.

| Condition | Models | Valid / all | Strict F1 | Valid | F1 (valid) |
| :--- | ---: | ---: | ---: | ---: | ---: |
| no format guide | 3 | 0/210 | 0.000 | 0.0% | n/a (no valid answer) |
| no format guide + grounding pack | 3 | 0/210 | 0.000 | 0.0% | n/a (no valid answer) |
| main | 15 | 784/1050 | 0.675 | 74.7% | 0.903 |
| main + grounding pack | 15 | 739/1050 | 0.634 | 70.4% | 0.898 |

**Table S18. Earlier-grader F1 against the score after a check of the picture, main condition (pilot run, preliminary, earlier grader).** *Earlier-grader F1*: the strict F1 from comparing scene trees. A valid scene that scores below 1 is rendered next to the reference (*pictures compared*). It is *counted right* if the two images are near-identical pixel for pixel, or if the image judge calls them the same. *F1 after picture check* is the earlier-grader F1 with the scenes that were counted right set to 1. The check never lowers a score.

| Model | Earlier-grader F1 | F1 after picture check | Change | Pictures compared | Counted right: pictures identical | Counted right: image judge says same | Judged different |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deepseek-v3.2 | 0.903 | 0.921 | +0.018 | 24 | 0 | 6 | 18 |
| deepseek-v4-flash | 0.859 | 0.870 | +0.011 | 21 | 4 | 3 | 14 |
| claude-haiku-4-5 | 0.857 | 0.877 | +0.020 | 25 | 0 | 3 | 22 |
| gemini-3.5-flash | 0.849 | 0.870 | +0.021 | 17 | 0 | 4 | 13 |
| minimax-m3 | 0.817 | 0.825 | +0.009 | 21 | 0 | 3 | 18 |
| qwen3-next-80b-a3b-instruct | 0.805 | 0.831 | +0.025 | 32 | 0 | 8 | 24 |
| glm-5.2 | 0.805 | 0.832 | +0.027 | 23 | 0 | 7 | 16 |
| llama-4-maverick | 0.792 | 0.799 | +0.007 | 8 | 1 | 2 | 5 |
| gemma-3-27b-it | 0.713 | 0.718 | +0.004 | 23 | 0 | 3 | 20 |
| kimi-k2.6 | 0.657 | 0.680 | +0.023 | 18 | 2 | 5 | 11 |
| gpt-5.4-nano | 0.654 | 0.682 | +0.028 | 42 | 18 | 4 | 20 |
| gpt-oss-120b | 0.561 | 0.574 | +0.012 | 19 | 0 | 5 | 14 |
| qwen3-30b-a3b-instruct-2507 | 0.519 | 0.529 | +0.010 | 13 | 0 | 4 | 9 |
| gpt-oss-20b | 0.252 | 0.256 | +0.003 | 6 | 0 | 1 | 5 |
| nemotron-3-super-120b-a12b | 0.078 | 0.079 | +0.001 | 2 | 0 | 1 | 1 |

**Table S19. Tokens and cost, main condition (pilot run, preliminary, earlier grader).** Tokens are as reported by the provider for the whole run of the model. Cost is in US dollars at list price on the day of the run; *not recorded* means no price was stored for that model, not that it was free. *Per 100 answers*: cost divided by the number of answers, times 100. Total for the 7 priced models: $0.65.

| Model | Weights | Strict F1 | Input tokens | Answer tokens | Cost | Per 100 answers |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| deepseek-v3.2 | open | 0.903 | 165,839 | 21,147 | $0.0453 | $0.065 |
| deepseek-v4-flash | open | 0.859 | 167,340 | 49,201 | not recorded | – |
| claude-haiku-4-5 | closed | 0.857 | 183,069 | 24,842 | $0.3073 | $0.439 |
| gemini-3.5-flash | closed | 0.849 | 173,809 | 75,935 | $0.2420 | $0.346 |
| minimax-m3 | open | 0.817 | 171,434 | 34,963 | not recorded | – |
| qwen3-next-80b-a3b-instruct | open | 0.805 | 163,196 | 17,203 | not recorded | – |
| glm-5.2 | open | 0.805 | 162,380 | 26,007 | not recorded | – |
| llama-4-maverick | open | 0.792 | 171,776 | 25,012 | not recorded | – |
| gemma-3-27b-it | open | 0.713 | 174,611 | 16,805 | $0.0167 | $0.024 |
| kimi-k2.6 | open | 0.657 | 159,811 | 96,179 | not recorded | – |
| gpt-5.4-nano | closed | 0.654 | 161,967 | 18,712 | $0.0156 | $0.022 |
| gpt-oss-120b | open | 0.561 | 166,380 | 44,204 | not recorded | – |
| qwen3-30b-a3b-instruct-2507 | open | 0.519 | 163,196 | 19,768 | $0.0099 | $0.014 |
| gpt-oss-20b | open | 0.252 | 166,348 | 58,094 | $0.0131 | $0.019 |
| nemotron-3-super-120b-a12b | open | 0.078 | 165,256 | 50,967 | not recorded | – |

### S8.1 The trial of the rating study

*Purpose.* To see whether answers that the earlier grader scored below 1 looked the same as
the reference to people, that is, to look for false fails, and to try out the image judge as
a way of finding them.

*What was done.* In October, each valid scene that scored below 1 was rendered, and an image
judge (a vision-language model; Section 5.5 of the paper) was shown its picture beside the
picture of the reference. Volunteers then judged a sample of the same picture comparisons. In
all, three raters, one of them an author, gave 114
verdicts of "same" or "different" on 109 picture comparisons.

*Result.* People and the image judge gave the same verdict in 79% of
cases. Cohen's kappa, which is agreement beyond what chance would give (0 is chance, 1 is
perfect), was 0.54 (95% interval 0.34 to
0.71). Where the judge had said "same", people agreed in
74% of cases (95% interval 57% to
89%), or in 62% (95% interval
40% to 85%) when the author's verdicts
are left out.

*Limits.* Only one of the three raters
met the attention-check rule that was written before the data were seen (at least
80% right on each kind of check item): the author was never shown a check
item, and one volunteer answered "can't tell" on a check, which the rule counts as a miss. The
numbers above include all raters and so depart from that rule. Only
5 picture comparisons received two verdicts, so agreement between
people cannot be estimated. The trial does not validate the image judge, and it supports no
statement about categories, single models or the final run. No score in the paper uses the
image judge. As a check of how much it could matter: under the earlier grader, counting the
judge's "same" verdicts as right would have changed no model's mean F1 by more than
0.028 (Table S18).

## S9. Further tables of the final run

⟦PENDING: final run — the tables that Section 6.5 of the paper points to, for both tracks: outcome counts per model (valid, unshowable by kind, schema-breaking, cut off), the JSON-repair counterfactual, F1 valid-only, cost per model, the one-sided pairs of Table 9 divided by whether the side that was not right was unshowable, and the first two rows of Table 10 with their difference and its interval for each model (Section 6.4)⟧

## S10. The corpus in detail

Sections S10 to S15 hold detail that the paper gives in one sentence each: rules, counts,
special cases and caveats. In these sections, a section, table, figure or box that is cited
without the letter S is one of the paper.

### S10.1 Disease proteins and the clinical tasks

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

### S10.2 The categories in detail

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

The 797 tasks (381 on the scene track, 416 on the
call-list track) use 78 of the 79 panel structures. No structure
appears in more than 6 tasks of one category and
track. The call-list track has more translation tasks than the scene track because its format
has many single-purpose calls and selectors. Of its 178 translation
tasks, 116 (from
18 templates) exercise calls that have no
counterpart in a scene; the other 62 are pairs.

### S10.3 The clinical category in detail

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
nomenclature [1, 2], but they are not complete HGVS descriptions:
a complete description names a versioned reference sequence, and a UniProt accession, which
46 requests state, is not one that HGVS accepts. ClinVar itself
states each change on a transcript, and we did not check which transcript its protein-level
name is counted on. SI Section S3.2 gives the details of both points, and Section S14.2 the
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
They are not the same property (Table 2).

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

With a name in UniProt numbering, copying is right exactly when there is no offset. The two
groupings differ only for the 13 traditional names. In
12 of them the entry is also numbered from the mature protein, so
the number in the name is the author number although the UniProt number is not. The one
remaining traditional name (E6V of haemoglobin beta, which
is p.Glu7Val) is asked on a predicted structure, which
uses UniProt numbering. There, copying the traditional number selects the wrong residue
although the target has no offset (the single task in the top-right cell of Table 2).

*Further properties.* Table S20 lists further properties of the clinical tasks. One needs a
remark. Where a request states no UniProt accession and names the variant with "p.", neither
the request nor the system prompt says which sequence the position is counted on. A reader of
a bare name with "p." would normally take it to be counted on the protein of the gene's MANE
Select transcript, the one transcript per gene that RefSeq and Ensembl jointly designate as
the default for clinical reporting [4]. We assume, and did not check, that
this protein is numbered as the UniProt canonical sequence is (Section S14.2).

**Table S20. Further properties of the 82 clinical tasks.** *Tasks*: number of tasks
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

### S10.4 The two formats in detail

The two formats differ in kind. A MolViewSpec scene [5] is *declarative*: a tree
that states what to load, which atoms form a *component* (a named set of selected atoms), and
how each component is drawn.
Nothing is on screen unless the scene says so. A call list is *imperative*: an ordered list of
calls to the PDBe Mol\* viewer, version 3.3.2 [6]. The viewer starts with the whole
structure drawn in a *default view*, and each call changes that state, so order matters. The
call list is written as a JSON list in a small notation of our own, which the format guide
documents (Section 5.2). Each item names one call or setting of the viewer and its arguments,
under the names that the viewer's Python notebook widget, ipymolstar 0.1.0 [7],
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
viewer rests on both using SIFTS (Section S14.3).

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

### S10.5 What a request may leave open

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

### S10.6 Set-aside structures and wording

MolBench tasks have been public since May 2026, so a model released later may have seen
earlier tasks. By *earlier* tasks and releases we mean those published before the present
corpus (the first version of the benchmark, Section 6). Two measures address this.

*Set-aside structures.* Before generation, 15 structures were
set aside: no release of the first version used them, and their tasks are reported apart. The
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
and do not test it, because the split is small (Section S14.4).

*Wording.* To measure sensitivity to wording, 30 requests on
structures outside the set-aside split have, beside their original (*full*) wording, two further phrasings each, a
*terse* one and an *indirect* one, with the same reference. For example, the request "Add chain B too, as a cartoon in grey." also exists in
a terse form ("chain B too, grey cartoon") and in an indirect form
("Could I see chain B as well? A grey cartoon would be fine."). Of the
30 requests, 11 are pairs, so they are
41 tasks, and two further phrasings of each give
82 additional task files. These are not counted in Table 1.

## S11. Grading in detail

Section S4 gives the grading rules themselves. This section gives the reasons, the counts and
the worked examples.

### S11.1 From an answer to a drawn state

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
by chain identifier, fails. This is the *text rule* of the name-resolution category. The
run records for each answer whether its entry is the reference entry, so results are
reported in two rows: answers on the reference entry, and answers on any other accepted
entry, nearly all of which fall under the text rule (Table 8).

On the call-list track the grader replays the calls in order, following the behaviour of PDBe
Mol\* 3.3.2, and compares the drawn state that they end in. Because that viewer draws the whole
structure as soon as it loads, the facts of a call-list answer are its *differences from the
default view*. Order matters, as it does in the viewer: a later call can undo an earlier one,
and the answer is graded on where it ends. SI Section S4 lists every rule on both tracks.

### S11.2 F1 and task success

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

### S11.3 The target score: which atoms, which convention, which tasks

**Target score: are the requested atoms marked out exactly?** The *target*
of a task is the atoms that the request is about. For most tasks the generator stores it with
the task. In a
clinical task it is the residue of the variant. In a task that asks for a feature against a
background ("grey cartoon and the biotin in green ball-and-stick") it is the feature, here the
biotin and not the cartoon; if several features are asked for, it is all of them. In a task
with no such distinction ("the whole protein as a yellow cartoon") it is everything the
reference draws.

The counts (wanted, credit, attempted, spill, extra), the three rules for extra drawing and
the formula are in Section S4.3.

The line between rules 2 and 3 is whether the added style is confined to the target. A second
representation on the target alone is read as another answer to "how should these atoms be
drawn?", and a style that also covers other atoms as background. The line is a convention,
and it has a cost that two rows of Table 3 show: ball-and-stick added to the residue alone
is penalised (row S9, 0.67), and the same
ball-and-stick added to the residue and its two neighbours is not (row
S10, 1.00). Task success and F1
penalise both.

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
fix the primary score of each table (Table S0f). Within a track, models are ranked by the task
success rate, and the target score is reported beside it. Between the two formats, models
are compared on the pairs only, and first on whether each answer is target-right (Section
5.4).

When a task lists several accepted answers (Section 3.3), an answer is graded against each,
and the best result counts.

### S11.4 The running example, worked by hand

*The two spill rows of Table 3.* The target score can be checked by hand, in
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

### S11.5 Outcomes and averages

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
  offline JSON repair library [8] and graded again. No model is called. The repaired
  score is reported beside the strict score and never replaces it.

### S11.6 The control set and the check in the running viewers

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

### S11.7 What is deliberately not graded

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

## S12. The experimental setup in detail

### S12.1 Models

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

### S12.2 Prompting conditions and the format guides

Table 5 lists the four prompting conditions. In each of them a model receives a system prompt
and the request, and returns one answer. A model cannot
look anything up, cannot ask a clarifying question, and does not see a rendered result. It is not
given the structure file. Both system prompts tell the model that its answer is judged by what
the viewer ends up showing; the scene prompt adds that anything drawn that was not asked for
counts against the answer.

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

### S12.3 Sampling

Each model answers each task three times in the main condition, at the provider's
default temperature. The limit on the length of an answer is 8,000 tokens.
Of the core models, seven first write reasoning text that the user does not
see; the provider bills it and counts it against the limit. For these models the limit is
16,000 tokens for reasoning and answer together (SI Table S7). An
invalid answer is scored as it stands and is not retried; only transport errors are retried.
Every raw answer is archived with its token counts, the reason the provider gives for the end
of the answer, and its cost.

### S12.4 Statistics

- **Per-model scores** are means over tasks of the mean over the task's 3
  answers. For task success this is the task success rate; the all-3 rate (the
  share of tasks on which all 3 answers succeed) is reported beside it (Section
  4.2). Valid-only scores are the exception: they pool a model's valid answers (Section 4.4).
  Means over models are means over the core models and the optional models that were run;
  they leave the two scripts out.
- **Intervals** are 95% bootstrap intervals [9] with 10,000
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
      are resampled as separate structures (Section S14.4).
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
      McNemar's exact test [10]. We report the four counts for every model. The
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

### S12.5 The rating study

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

A smaller trial of the study has been run on the pilot answers (Section S13.1, Finding 6).

### S12.6 Reproducibility

One command performs the run from the manifest. It does not start if the projected cost is
above a cap in US dollars that the manifest states, and it stops if spending would pass it.
One command rebuilds every table, figure and number in this paper from the archived answers.
A rehearsal with a mock model exercises the whole path at no cost. Grading needs no network
access and no paid service.

## S13. The first version of the benchmark: pilot findings and errors

### S13.1 The six findings of the pilot runs in full

MolBench has had two versions, and this paper names them in one way throughout. The *first
version* is the benchmark as it was public from May 2026 until the present corpus replaced
it. At the time of its last run it had a corpus of 70 scene
tasks on 14 structures, 20 hand-written call-list
tasks, and two graders that compared text (Section 4.5). Two of its runs are used in this
paper: one of the call-list tasks in July 2026, and one of the scene tasks in October 2026,
which we call the *pilot run*. The *present version* is the benchmark of Sections 3 and 4.

Section 6.6 of the paper gives Findings 1 and 2 and names the others. All six follow in full.

**Everything in this section is preliminary.** Findings 1 to 4 come from a pilot run of
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
from 0.07 to 0.84 (Table S21, columns *Valid answers*
and *F1, strict*). The two are nearly proportional: the Pearson correlation between a
model's share of valid answers and its strict F1 is r = 0.99
(15 models). With the strict task success rate, by which Table S21 is
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

**Table S21. Pilot run, per model (preliminary).** The run had 70 tasks and one
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
135 answers (Table S22, Figure 6). The natural reading is that finding the
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
drew the right residue" is therefore a statement about drawing, not about mapping. Table S23
(rows 1 and 2) says what replaced both.

**Table S22. Pilot run by category, all models pooled (preliminary).** *Answers*: one per model
and task. *Valid*: answers that parse and that the viewer accepts. *F1, earlier grader*: the
score under the grader used in October, for comparison. *F1* and *task success rate*: as in
Table S21, strict, over all answers of the row. *Requested part exactly right*: this column has its
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

Figure 6 of the paper shows the three scores of Table S22 by category.

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

### S13.2 Nine errors in the first version and what replaced each

The first version of MolBench (defined in Section 6) was wrong in nine ways that we know of. Table S23 lists each error, how
we found out, and what replaced it in the present version, because each error is one that
another benchmark of this kind could make.

**Table S23. Nine errors in the first version of MolBench and what replaced each in the
present version.**
*Where*: the sections that give the numbers behind the row.

| Row | What was wrong | How we found out | What replaced it | Where |
|--:|:--------|:------|:--------|:----|
| 1 | Our clinical references drew a cartoon that no request asked for, and we read the low score that followed as a difficulty of finding the residue. | A breakdown of where valid answers lost their points (Section 6.6, Finding 2). | A reference holds only what the request states. If context is wanted, the request asks for it in words. Every task stores its target where it has one, and the target score is reported beside task success in Tables 6 to 10. | Sections 3.2, 4.2; 6.6, Finding 2 |
| 2 | The clinical category could not test the mapping: all its tasks sat on one protein whose structure uses UniProt numbering. | The same analysis. | 82 tasks on 25 proteins and 31 structures; in 59 tasks the target has an offset, and results are grouped by whether copying the number in the variant name is right (it is wrong in 48). | Section 3.3.1; 6.6, Finding 2 |
| 3 | "Pathogenic" was taken from a secondary source: we first took the variants that UniProt lists as pathogenic. | A check of each candidate against the ClinVar records that UniProt cross-references. For 20% of the candidates none of these records gives the same amino-acid change a pathogenic or likely pathogenic aggregate classification, and ClinVar's aggregate classification of some variants named in tasks of the first version is "conflicting classifications of pathogenicity". | A variant is used only if ClinVar holds a record of that gene and that one change with a pathogenic or likely pathogenic classification and stated criteria (one exception, SI Section S3.2). The dates are stored. | Section 3.1; SI Section S3.2 |
| 4 | Both graders compared text: scene trees path by path, call sequences field by field. They rejected correct answers that were merely written differently, both passed some wrong ones (the scene grader 3%, the call-list grader 21%), and on the call-list track a keyword script scored close to the models. | The control set. | Both tracks are graded on drawn state, and the control set is run as a test on every change. | Section 4.5, Table 4; SI Section S13.1, Finding 5 |
| 5 | Hand-written call-list tasks had errors: label numbers where author numbers were meant, and one task that was the worked example of the prompt. | A check of those references against the structures. | Every reference is generated; a sample of references is replayed in the viewer itself; and the entry used for the worked example of both system prompts is excluded from the corpus. | Sections 3.2, 3.7 |
| 6 | Some requests had no single answer. A request to highlight "all pathogenic residues" of one protein resolved to far more residues than any user means; "show me lysozyme" was graded against one arbitrary view. | Reading the references. | Clinical requests name each variant. Requests with a countable ambiguity have their own category, with every accepted answer listed. Open-ended requests are left out. | Sections 3.3, S14.1 |
| 7 | Raters could not see what they were rating. A single highlighted residue on a whole complex was a few pixels wide, and a volunteer flagged a reference as wrong when it was only unreadable. A volunteer also found references in which two cartoons overlapped. | The trial of the rating study. | Pictures are framed on the target atoms from one shared camera. The overlapping references were corrected. The next study completes two ratings of a picture comparison before it opens new ones. | Section 5.5; SI Section S13.1, Finding 6 |
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

## S14. Limitations in full

Four limits bound the claims of this paper more than the others: each track is graded by the
rules of one viewer; the requests come from templates; the tasks are public; and the grader
has been tested only against cases that we foresaw. The full list follows in four groups.

### S14.1 Scope

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

### S14.2 Corpus

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

### S14.3 Grader

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
  fails (the text rule of Section 4.1). Table 8 reports such answers in a row of their
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

### S14.4 Run

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

## S15. Related work in detail; licences

### S15.1 Benchmarks that score the operation of scientific software

**ScienceBoard** [11] is the closest published benchmark. It has 169 tasks in
six domains, performed by agents that operate a desktop through screenshots and clicks. Its
biochemistry domain uses UCSF ChimeraX [12], and a task is checked by reading
the state of the application after the agent has finished. MolBench shares the idea of checking
the resulting state. It differs in four ways. It tests the step from request to commands
directly, with no desktop in between. Its references are computed by script and record their
origin. Four of its categories of task differ in what the model must know beyond the request, and
one of these asks about clinical variants. And it poses requests in two answer formats.

**SciVisAgentBench** [13] has 108 expert-written cases of scientific
visualization; its molecular cases use GROMACS and VMD. Outcomes are scored by a language-model
judge against written rubrics, with deterministic checks for some suites. The authors compared
the judge with 12 visualization experts and report an agreement among raters (Krippendorff's
alpha) of 0.669 and a correlation between judge and human scores of about 0.81. MolBench is
narrower and stricter: it covers only molecular viewers, and its scores need no judge model.

**OSWorld-Science** [14] follows the OSWorld desktop benchmark
[15] with 146 tasks over scientific applications, one of which combines PyMOL with a
nuclear magnetic resonance package. Evaluators inspect application state and output files and
give partial credit. The overlap with MolBench is small: a molecular viewer is one application
among many, and the tasks test the operation of a graphical interface.

General benchmarks of tool use, such as ToolLLM [16] and tau-bench
[17], measure whether a model calls the right function with the right arguments.
Our call-list track has that shape. The difference is the check: a viewer call is right only
if its selection resolves to the right atoms in a particular structure.

### S15.2 Assistants for molecular viewers

**Speak to a Protein** [18] is an assistant that answers questions about a
protein while driving a browser viewer built on the Mol\* engine [19]. Its
evaluation covers question answering; the paper lists viewer operations as a task group and
reports no accuracy for them. **ChatMol Copilot** [20] is an agent for molecular
modelling that can also operate PyMOL. **ChimeraX** can be operated from a chat assistant
through a built-in tool server; its documentation notes that the assistant "will often make
mistakes" [21]. **VOICE** [22] and a speech interface for an immersive
molecular-graphics application [23] operate molecular scenes by spoken language
and were evaluated with users, not with scored tasks. The Mol\* project has merged an optional
assistant and a command layer into its next viewer [24]; we found no published
benchmark from that work. A community tool that builds MolViewSpec scenes from chat
[25] states in its documentation that the residue numbers researchers take from
ClinVar, publications and mutation databases "are always author numbers". That holds for some
entries and fails for many [26]. It is the error our clinical category is built to
detect.

### S15.3 The data and software MolBench stands on

MolViewSpec describes a molecular scene as a tree of typed nodes and is implemented as an
extension of the Mol\* viewer [5, 19, 27]. The
call-list track targets the PDBe build of Mol\* [6], which a notebook widget exposes
to Python [7]. Structures come from the Protein Data Bank [28] and, for
5 predicted structures, from the AlphaFold Protein Structure Database [29, 30]. The mapping between UniProt residues and the residues of a structure
comes from SIFTS [31], as distributed by PDBe [32, 33]. Variants
and their clinical classification come from ClinVar [34], found through UniProt
[35]. Structure files are read with GEMMI [36].

The numbering problem at the centre of the clinical category has been met from another direction.
Vollmar and colleagues find residue mentions in the crystallographic literature and map them to
structures through SIFTS [37]. Their system reads papers; ours asks whether a
language model can do the same mapping when it writes a scene. MiSI-Bench [38] asks
vision-language models questions about rendered images of molecules and finds them well below
human level, which is one reason our scores do not rest on a model that looks at pictures.

Where this section says that another work lacks something, we mean that we did not find it in
the cited source.

### S15.4 Licences of data and software

**Licences of data and software.** We read each licence at its source on 16 November 2026 (Table
16). Frozen copies of third-party data in the repository keep their original terms and are
attributed in the repository.

**Table S24. Data and software used, with licence or terms as stated at the source.**

| Resource | Used for | Licence or terms | Read at |
|:---|:---|:---|:---|
| Protein Data Bank archive and RCSB PDB web services [28] | structure files, atom tables, entry annotations | CC0 1.0 public-domain dedication | rcsb.org/pages/usage-policy |
| PDBe: SIFTS mapping, updated structure files, search of entries per protein [31, 33] | residue mapping, choice of structures | EMBL-EBI terms of use: no additional restrictions on use or redistribution; attribution expected | ebi.ac.uk/about/terms-of-use |
| UniProt [35] | sequences, candidate variants | CC BY 4.0 | uniprot.org/help/license |
| ClinVar [34] | classification of variants | NCBI molecular data policy: NCBI places no restrictions on use or distribution; submitters may hold rights | ncbi.nlm.nih.gov/home/about/policies |
| AlphaFold Protein Structure Database [29, 30] | 5 predicted structures | CC BY 4.0 | alphafold.ebi.ac.uk (licence and disclaimer) |
| Mol\* [19] and MolViewSpec [5] | scene format, validation, read-back, pictures | MIT | github.com/molstar |
| PDBe Mol\* [6] | viewer of the call-list track | Apache-2.0 | github.com/molstar/pdbe-molstar |
| ipymolstar [7] | Python host of that viewer | MIT | pypi.org/project/ipymolstar |
| GEMMI [36] | reading structure files | MPL-2.0 | github.com/project-gemmi/gemmi |
| json-repair [8] | repair counterfactual | MIT | github.com/mangiucugna/json_repair |

MolBench's own code, tasks and references are released under the MIT licence.

## References

1. den Dunnen JT, Dalgleish R, Maglott DR, Hart RK, Greenblatt MS, McGowan-Jordan J, Roux AF, Smith T et al. HGVS Recommendations for the Description of Sequence Variants: 2016 Update. *Human Mutation* 2016;37(6):564–569. doi:[10.1002/humu.22981](https://doi.org/10.1002/humu.22981)
2. Hart RK, Fokkema IFAC, DiStefano M, Hastings R, Laros JFJ, Taylor R, Wagner AH, den Dunnen JT. HGVS Nomenclature 2024: improvements to community engagement, usability, and computability. *Genome Medicine* 2024;16(1):149. doi:[10.1186/s13073-024-01421-5](https://doi.org/10.1186/s13073-024-01421-5)
3. Pepys MB, Hawkins PN, Booth DR, Vigushin DM, Tennent GA, Soutar AK, Totty N, Nguyen O et al. Human lysozyme gene mutations cause hereditary systemic amyloidosis. *Nature* 1993;362(6420):553–557. doi:[10.1038/362553a0](https://doi.org/10.1038/362553a0)
4. Morales J, Pujar S, Loveland JE et al. A joint NCBI and EMBL-EBI transcript set for clinical genomics and research. *Nature* 2022;604(7905):310–315. doi:[10.1038/s41586-022-04558-8](https://doi.org/10.1038/s41586-022-04558-8)
5. Midlik A, Bittrich S, Fleming JR, Nair S, Velankar S, Burley SK, Young JY, Vallat B et al. MolViewSpec: a Mol* extension for describing and sharing molecular visualizations. *Nucleic Acids Research* 2025;53(W1):W408–W414. doi:[10.1093/nar/gkaf370](https://doi.org/10.1093/nar/gkaf370)
6. PDBe. PDBe Molstar (pdbe-molstar): the PDBe implementation of Mol*, version 3.3.2. *Software, Apache-2.0; version 3.3.2 published on npm 2024-11-25*. <https://github.com/molstar/pdbe-molstar>
7. Smit J, ipymolstar contributors. ipymolstar: Mol* as an anywidget, version 0.1.0. *Software, MIT; version 0.1.0 released on PyPI 2025-04-10*. <https://github.com/molstar/ipymolstar>
8. Baccianella S. json_repair: repair malformed JSON from LLMs, APIs, logs, and user input in Python. *Software, MIT* 2026. <https://github.com/mangiucugna/json_repair>
9. Efron B. Bootstrap Methods: Another Look at the Jackknife. *The Annals of Statistics* 1979;7(1):1–26. doi:[10.1214/aos/1176344552](https://doi.org/10.1214/aos/1176344552)
10. McNemar Q. Note on the Sampling Error of the Difference Between Correlated Proportions or Percentages. *Psychometrika* 1947;12(2):153–157. doi:[10.1007/BF02295996](https://doi.org/10.1007/BF02295996)
11. Sun Q, Liu Z, Ma C, Ding Z, Xu F, Yin Z, Zhao H, Wu Z et al. ScienceBoard: Evaluating Multimodal Autonomous Agents in Realistic Scientific Workflows. *arXiv preprint* 2025. v3 is marked “ICLR 2026 Camera Ready Version”. arXiv:[2505.19897](https://arxiv.org/abs/2505.19897)
12. Goddard TD, Huang CC, Meng EC, Pettersen EF, Couch GS, Morris JH, Ferrin TE. UCSF ChimeraX: Meeting modern challenges in visualization and analysis. *Protein Science* 2018;27(1):14–25. doi:[10.1002/pro.3235](https://doi.org/10.1002/pro.3235)
13. Ai K, Miao H, Tang K, Gorski N, Sun J, Liu G, Ingolfsson HI, Lenz D et al. SciVisAgentBench: A Benchmark for Evaluating Scientific Data Analysis and Visualization Agents. *arXiv preprint* 2026. arXiv comment: IEEE Transactions on Visualization and Computer Graphics (IEEE VIS '26). arXiv:[2603.29139](https://arxiv.org/abs/2603.29139)
14. Dai D, Qi H, Liu L, Li Y, Chen B, Dou Z, Zeng Q, Kang Q et al. OSWorld-Science: A Benchmark of Computer Use Agents for Learning and Using Scientific Software. *arXiv preprint* 2026. arXiv:[2609.39903](https://arxiv.org/abs/2609.39903)
15. Xie T, Zhang D, Chen J, Li X, Zhao S, Cao R, Toh JH, Cheng Z et al. OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments. *arXiv preprint* 2024. arXiv:[2404.07972](https://arxiv.org/abs/2404.07972)
16. Qin Y, Liang S, Ye Y, Zhu K, Yan L, Lu Y, Lin Y, Cong X et al. ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs. *arXiv preprint* 2023. arXiv:[2307.16789](https://arxiv.org/abs/2307.16789)
17. Yao S, Shinn N, Razavi P, Narasimhan K. tau-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains. *arXiv preprint* 2024. arXiv:[2406.12045](https://arxiv.org/abs/2406.12045)
18. Navarro C, Torrens-Fontanals M, Thölke P, Doerr S, De Fabritiis G. Speak to a Protein: An Interactive Multimodal Co-Scientist for Protein Analysis. *Journal of Chemical Information and Modeling* 2026;66(19):12391–12401. Preprint: arXiv:2510.17826. doi:[10.1021/acs.jcim.6c01738](https://doi.org/10.1021/acs.jcim.6c01738)
19. Sehnal D, Bittrich S, Deshpande M, Svobodová R, Berka K, Bazgier V, Velankar S, Burley SK et al. Mol* Viewer: modern web app for 3D visualization and analysis of large biomolecular structures. *Nucleic Acids Research* 2021;49(W1):W431–W437. doi:[10.1093/nar/gkab314](https://doi.org/10.1093/nar/gkab314)
20. Sun J, Li A, Deng Y, Li J. ChatMol Copilot: An Agent for Molecular Modeling and Computation Powered by LLMs. *Proceedings of the 1st Workshop on Language + Molecules (L+M 2024)*:55–65. doi:[10.18653/v1/2024.langmol-1.7](https://doi.org/10.18653/v1/2024.langmol-1.7)
21. Goddard T. Claude Chat to operate ChimeraX. *UCSF RBVI web page, 4 December 2025*. <https://www.rbvi.ucsf.edu/chimerax/data/claude-dec2025/claude_mcp.html>
22. Jia D, Irger A, Besançon L, Strnad O, Luo D, Björklund J, Kouyoumdjian A, Ynnerman A et al. VOICE: Visual Oracle for Interaction, Conversation, and Explanation. *IEEE Transactions on Visualization and Computer Graphics* 2025;31(10):8828–8845. Preprint: arXiv:2304.04083. doi:[10.1109/TVCG.2025.3579956](https://doi.org/10.1109/TVCG.2025.3579956)
23. Cortes Rodriguez F, Abriata L. Speech recognition assisted by large language models to command software orally -- Application to an augmented and virtual reality web app for immersive molecular graphics. *arXiv preprint* 2026. arXiv:[2603.02901](https://arxiv.org/abs/2603.02901)
24. Mol* developers. Prism viewer (pull request 1978) and v6: PyMOL and VMD commands (pull request 2052), molstar/molstar. *Source-code pull requests, merged 2026-10-16 and 2026-10-25*. <https://github.com/molstar/molstar/pull/1978>
25. RenhaoL. molstar-mcp: a Model Context Protocol server that builds MolViewSpec scenes for Mol*. *Software, MIT; repository created 2026-05-31*. <https://github.com/RenhaoL/molstar-mcp>
26. Faezov B, Dunbrack RL. PDBrenum: A webserver and program providing Protein Data Bank files renumbered according to their UniProt sequences. *PLOS ONE* 2021;16(7):e0253411. doi:[10.1371/journal.pone.0253411](https://doi.org/10.1371/journal.pone.0253411)
27. Bittrich S, Midlik A, Varadi M, Velankar S, Burley SK, Young JY, Sehnal D, Vallat B. Describing and Sharing Molecular Visualizations Using the MolViewSpec Toolkit. *Current Protocols* 2024;4(7):e1099. doi:[10.1002/cpz1.1099](https://doi.org/10.1002/cpz1.1099)
28. wwPDB consortium. Protein Data Bank: the single global archive for 3D macromolecular structure data. *Nucleic Acids Research* 2019;47(D1):D520–D528. doi:[10.1093/nar/gky949](https://doi.org/10.1093/nar/gky949)
29. Varadi M, Bertoni D, Magana P, Paramval U, Pidruchna I, Radhakrishnan M, Tsenkov M, Nair S et al. AlphaFold Protein Structure Database in 2024: providing structure coverage for over 214 million protein sequences. *Nucleic Acids Research* 2024;52(D1):D368–D375. doi:[10.1093/nar/gkad1011](https://doi.org/10.1093/nar/gkad1011)
30. Jumper J, Evans R, Pritzel A, Green T, Figurnov M, Ronneberger O, Tunyasuvunakool K, Bates R et al. Highly accurate protein structure prediction with AlphaFold. *Nature* 2021;596(7873):583–589. doi:[10.1038/s41586-021-03819-2](https://doi.org/10.1038/s41586-021-03819-2)
31. Dana JM, Gutmanas A, Tyagi N, Qi G, O'Donovan C, Martin M, Velankar S. SIFTS: updated Structure Integration with Function, Taxonomy and Sequences resource allows 40-fold increase in coverage of structure-based annotations for proteins. *Nucleic Acids Research* 2019;47(D1):D482–D489. doi:[10.1093/nar/gky1114](https://doi.org/10.1093/nar/gky1114)
32. PDBe-KB consortium. PDBe-KB: a community-driven resource for structural and functional annotations. *Nucleic Acids Research* 2020;48(D1):D344–D353. doi:[10.1093/nar/gkz853](https://doi.org/10.1093/nar/gkz853)
33. PDBe-KB consortium. PDBe-KB: collaboratively defining the biological context of structural data. *Nucleic Acids Research* 2022;50(D1):D534–D542. doi:[10.1093/nar/gkab988](https://doi.org/10.1093/nar/gkab988)
34. Landrum MJ, Lee JM, Benson M, Brown GR, Chao C, Chitipiralla S, Gu B, Hart J et al. ClinVar: improving access to variant interpretations and supporting evidence. *Nucleic Acids Research* 2018;46(D1):D1062–D1067. doi:[10.1093/nar/gkx1153](https://doi.org/10.1093/nar/gkx1153)
35. The UniProt Consortium. UniProt: the Universal Protein Knowledgebase in 2025. *Nucleic Acids Research* 2025;53(D1):D609–D617. doi:[10.1093/nar/gkae1010](https://doi.org/10.1093/nar/gkae1010)
36. Wojdyr M. GEMMI: A library for structural biology. *Journal of Open Source Software* 2022;7(73):4200. doi:[10.21105/joss.04200](https://doi.org/10.21105/joss.04200)
37. Vollmar M, Westrip S, Nair S, Balasubramaniyan B, Velankar S, Jones L, Strickland P. Associating protein residues in the literature with structural data. *Acta Crystallographica Section D Structural Biology* 2026;82(2):113–125. doi:[10.1107/S2059798326000021](https://doi.org/10.1107/S2059798326000021)
38. Li Z, Kong X, Su J, Ma Z, Li M, Li S, Zhang Y, Rong Y et al. From Macro to Micro: Benchmarking Microscopic Spatial Intelligence on Molecules via Vision-Language Models. *arXiv preprint* 2025. arXiv:[2512.10867](https://arxiv.org/abs/2512.10867)
