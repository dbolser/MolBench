<!-- Built by paper/build.py from paper/si/ and paper/generated/*.json (run numbers: October 2026 panel, PRELIMINARY). Do not edit: edit the sources. -->

# Supporting Information

**MolBench: Grading Language Models on What a Molecular Viewer Would Show**

This file accompanies the paper. Every table in it is written by script from the task files,
the frozen data or archived model answers. Terms are used as defined in Boxes 1 and 2 of the paper:
*scene track* (answers are MolViewSpec scenes), *call-list track* (answers are ordered calls to
the PDBe Mol\* viewer), *drawn state*, *style*, *fact*, *F1*, *task success*, *target score*, *strict*
and *valid-only*. *Model* always means a language model. The repository's own grading
document calls a style a *draw* and a category a *tier*; the rules are the same. Task identifiers are those of the task files; in them the endings `-mvs` and
`-api` mark the scene track and the call-list track.

Contents: S0, background terms of structural biology · S1, the running example in full · S2,
all task templates · S3, the structure panel and the variant list · S4, grading rules and
known limits · S5, the control set by kind · S6, the run manifest, models and prices · S7,
the system prompts · S8, further tables of the pilot run, and the trial of the rating study ·
S9, further tables of the final run (pending).

## S0. Background terms of structural biology

For readers from outside structural biology. Box 1 of the paper defines the terms of
sequences and variants (UniProt, ClinVar, transcript, missense variant, mature protein) and
the terms of the corpus; Box 2 defines the terms of grading.

**Table S0. Background terms.**

| Term | Meaning |
|:---------|:------------------------------|
| Residue, chain | A protein is a chain of amino acids. One amino acid in the chain is a *residue*; residues are numbered along the chain. A structure file names each chain with a short identifier, often one letter. |
| C-alpha | The central carbon atom of an amino acid, to which its side chain is attached. One C-alpha per residue traces the course of the chain. |
| Polymer | The protein, DNA or RNA chains of a structure, as opposed to bound small molecules, ions and water. |
| Structure, entry | A set of atom coordinates. An *entry* is one deposition in the Protein Data Bank (PDB), with a four-character identifier such as 2NWD; where an entry holds several coordinate sets we use the first. A *predicted structure* is one computed from the sequence; ours come from the AlphaFold Protein Structure Database. |
| mmCIF | The file format of the PDB archive: tables of named columns, one row per atom in the table of atoms. |
| Ligand, het group | A *ligand* is a small molecule bound to the protein. *Het group* is the older file term for any molecule in an entry that is not part of a polymer chain (a ligand, an ion, a water); each kind has an identifier of up to three characters, such as HEM for haem. |
| Helix, strand | The two common local shapes of a protein chain. An entry records where each helix and each strand begins and ends. |
| Disulfide bond | A link between the sulfur atoms of two cysteine residues. |
| Representation | A way of drawing atoms: *cartoon* (a ribbon that traces the chain), *ball-and-stick*, *spacefill* (every atom as a full-size sphere), *surface*. |
| Selection | The expression in an answer that picks atoms, for example "chain X, residue 64". |
| Alternate positions | The same atom recorded at two or more positions, where the experiment saw a residue in more than one pose (the file calls these alternate conformers). |

## S1. The running example in full

The request, the two reference answers, the further accepted answers on the call-list track,
the stored target and the grounding pack, exactly as they are in the task files
`clin-pair-target-lyz-2nwd-w82r-mvs` (scene track) and `clin-pair-target-lyz-2nwd-w82r-api` (call-list track). The variant is
*LYZ* p.W82R (p.Trp82Arg; UniProt P61626). UniProt names the disease
as "Familial visceral amyloidosis, Ostertag type (AMYLD2)". ClinVar holds 2 records of this protein change, one
for each DNA change that causes it: VCV000014376, NM_000239.3(LYZ):c.244T>C (p.Trp82Arg); VCV000014378, NM_000239.3(LYZ):c.244T>A (p.Trp82Arg). Both carry the aggregate
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
score*: the requested atoms are drawn as asked, whatever else was drawn (0 to 1). Rows S1 to S10 are scenes, rows C1 to C5 call lists. *Spill*, *extra on the target* and *context* are the three rules for extra
drawing of Section S4.3.

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

## S2. Task templates

A template fixes what is asked; a seeded generator fills in the structure, the residues, the
colours and the wording. The corpus has 129 templates.

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
| Interactions | `in-ca-distance` | 5 | – | Show 1AKE as a yellow cartoon. Add a distance measurement (dashed line with the value as label) from the CA atom of Ser183 to the CA atom of Lys200. Both residues are… |
| Interactions | `in-computed` | 5 | – | 1A6M: grey cartoon; heme as red ball-and-stick with its computed non-covalent interactions shown; camera on the heme. |
| Interactions | `in-disulfide` | 5 | – | In 1F88 (grey cartoon), measure the S-S bond of the disulfide between Cys110 and Cys187: the two cysteines in green ball-and-stick, a labelled dashed line between thei… |
| Interactions | `in-hbond` | 5 | – | 1A3K: grey cartoon; Asn174 and Arg224 as magenta ball-and-stick; measure the hydrogen bond between OD1 of Asn174 and NH1 of Arg224 with a labelled dashed line; focus t… |
| Interactions | `in-ligand-contact` | 5 | – | 1ATP: grey cartoon; ATP as teal ball-and-stick; Phe54 as cyan ball-and-stick; measure the contact between ATP atom O2B and N of Phe54 with a labelled dashed line; focu… |
| Interactions | `in-metal-contact` | 5 | – | 1HRC: grey cartoon; heme as plum ball-and-stick; His18 and Met80 as salmon ball-and-stick; measure the distance from the heme iron to NE2 of His18 and SD of Met80 with… |
| Interactions | `in-salt-bridge` | 5 | – | Load 1EMA as a grey cartoon. Show Lys3 and Glu90 as cyan ball-and-stick, draw the salt bridge between the NZ atom of Lys3 and the OE1 atom of Glu90 as a dashed line la… |
| Interactions | `in-transparent` | 5 | – | Show 1CTQ with a semi-transparent brown protein surface (opacity 0.5) so that the GppNHp, drawn in steel blue ball-and-stick, can be seen through it. |
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
3. *Disease proteins.* 27 human proteins in which missense variants
   cause inherited disease are listed by UniProt accession. The list was written by hand:
   familiar examples that have experimental structures. For each, candidate entries are all PDB entries that SIFTS maps to the accession.
   The script keeps X-ray entries at 2.5 Å or better that cover at least one variant position
   (failing that, X-ray or cryo-electron microscopy entries at 3.5 Å or better), drops entries
   above the size limit or with several coordinate sets, and then chooses by, in order: most
   variant positions covered, fewest engineered mutations, fewest polymer entities, best
   resolution. Whether the author numbering differs from UniProt was not a criterion. A
   variant may also be asked on any other panel structure of the same protein.
4. *5 predicted structures* from the AlphaFold Protein Structure Database,
   numbered as UniProt is by construction: of p53, gamma-crystallin D, calmodulin-1, lysozyme and haemoglobin beta. The predicted
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
position (a dash: no protein chain mapped to UniProt). *Split*: public, or held back
(structures used only by held-back tasks; Section 3.6 of the paper). *Tasks*: tasks of the
corpus on this structure, both tracks, without rephrasings.

| Entry | Title (as deposited) | Method | Deposited | Atoms | Author numbering differs from UniProt | Split | Tasks |
|:---|:------------|:----|:----|---:|:---|:---|---:|
| 1A3K | X-RAY CRYSTAL STRUCTURE OF THE HUMAN GALECTIN-3 CARBOHYDRATE RECOGNITION DOMAIN (CRD) A… | X-ray 2.10 Å | 1998-01-22 | 1253 | no | public | 8 |
| 1A6M | OXY-MYOGLOBIN, ATOMIC RESOLUTION | X-ray 1.00 Å | 1998-02-26 | 1584 | yes | public | 9 |
| 1AAY | ZIF268 ZINC FINGER-DNA COMPLEX | X-ray 1.60 Å | 1997-01-18 | 1330 | yes | public | 9 |
| 1AKE | STRUCTURE OF THE COMPLEX BETWEEN ADENYLATE KINASE FROM ESCHERICHIA COLI AND THE INHIBIT… | X-ray 2.00 Å | 1991-11-08 | 3816 | no | public | 9 |
| 1AKI | THE STRUCTURE OF THE ORTHORHOMBIC FORM OF HEN EGG-WHITE LYSOZYME AT 1.5 ANGSTROMS RESOL… | X-ray 1.50 Å | 1997-05-19 | 1079 | yes | public | 6 |
| 1AOI | COMPLEX BETWEEN NUCLEOSOME CORE PARTICLE (H3,H4,H2A,H2B) AND 146 BP LONG DNA FRAGMENT | X-ray 2.80 Å | 1997-07-03 | 12385 | yes | public | 9 |
| 1ATP | 2.2 angstrom refined crystal structure of the catalytic subunit of cAMP-dependent prote… | X-ray 2.20 Å | 1993-01-08 | 3070 | yes | public | 12 |
| 1BNA | STRUCTURE OF A B-DNA DODECAMER. CONFORMATION AND DYNAMICS | X-ray 1.90 Å | 1981-01-26 | 566 | – | public | 8 |
| 1C3W | BACTERIORHODOPSIN/LIPID COMPLEX AT 1.55 A RESOLUTION | X-ray 1.55 Å | 1999-07-28 | 2073 | yes | public | 11 |
| 1CBS | CRYSTAL STRUCTURE OF CELLULAR RETINOIC-ACID-BINDING PROTEINS I AND II IN COMPLEX WITH A… | X-ray 1.80 Å | 1994-09-28 | 1213 | yes | public | 10 |
| 1CRN | WATER STRUCTURE OF A HYDROPHOBIC PROTEIN AT ATOMIC RESOLUTION. PENTAGON RINGS OF WATER… | X-ray 1.50 Å | 1981-04-30 | 327 | no | public | 5 |
| 1CTQ | STRUCTURE OF P21RAS IN COMPLEX WITH GPPNHP AT 100 K | X-ray 1.26 Å | 1999-08-20 | 1655 | no | public | 12 |
| 1D3Z | UBIQUITIN NMR STRUCTURE | NMR | 1999-10-01 | 1231 | yes | public | 3 |
| 1D5R | Crystal Structure of the PTEN Tumor Suppressor | X-ray 2.10 Å | 1999-10-11 | 2968 | no | public | 6 |
| 1EHZ | The crystal structure of yeast phenylalanine tRNA at 1.93 A resolution | X-ray 1.93 Å | 2000-02-23 | 1821 | – | held back | 3 |
| 1EMA | GREEN FLUORESCENT PROTEIN FROM AEQUOREA VICTORIA | X-ray 1.90 Å | 1996-08-01 | 1866 | no | public | 8 |
| 1F88 | CRYSTAL STRUCTURE OF BOVINE RHODOPSIN | X-ray 2.80 Å | 2000-06-29 | 5267 | no | public | 13 |
| 1FS3 | CRYSTAL STRUCTURE OF WILD-TYPE BOVINE PANCREATIC RIBONUCLEASE A | X-ray 1.40 Å | 2000-09-08 | 1066 | yes | held back | 3 |
| 1HHO | STRUCTURE OF HUMAN OXYHAEMOGLOBIN AT 2.1 ANGSTROMS RESOLUTION | X-ray 2.10 Å | 1983-06-10 | 2396 | yes | public | 20 |
| 1HK0 | Human GammaD Crystallin Structure at 1.25 A Resolution | X-ray 1.25 Å | 2003-03-05 | 1772 | yes | public | 11 |
| 1HRC | HIGH-RESOLUTION THREE-DIMENSIONAL STRUCTURE OF HORSE HEART CYTOCHROME C | X-ray 1.90 Å | 1994-08-16 | 993 | yes | public | 9 |
| 1HSG | CRYSTAL STRUCTURE AT 1.9 ANGSTROMS RESOLUTION OF HUMAN IMMUNODEFICIENCY VIRUS (HIV) II… | X-ray 2.00 Å | 1995-03-31 | 1686 | yes | not used (worked example of the call-list prompt) | 0 |
| 1HVR | RATIONAL DESIGN OF POTENT, BIOAVAILABLE, NONPEPTIDE CYCLIC UREAS AS HIV PROTEASE INHIBI… | X-ray 1.80 Å | 1994-02-14 | 1890 | yes | public | 10 |
| 1IEP | CRYSTAL STRUCTURE OF THE C-ABL KINASE DOMAIN IN COMPLEX WITH STI-571. | X-ray 2.10 Å | 2001-04-10 | 4710 | no | public | 14 |
| 1IGT | STRUCTURE OF IMMUNOGLOBULIN | X-ray 2.80 Å | 1996-10-25 | 12956 | yes | held back | 10 |
| 1IRO | RUBREDOXIN (OXIDIZED, FE(III)) AT 1.1 ANGSTROMS RESOLUTION | X-ray 1.10 Å | 1995-12-13 | 858 | no | public | 5 |
| 1K4C | Potassium Channel KcsA-Fab complex in high concentration of K+ | X-ray 2.00 Å | 2001-10-07 | 4534 | yes | public | 7 |
| 1KF1 | Structure and Packing of Human Telomeric DNA | X-ray 2.10 Å | 2001-11-19 | 536 | – | public | 3 |
| 1L2Y | NMR Structure of Trp-Cage Miniprotein Construct TC5b | NMR | 2002-02-25 | 304 | – | public | 2 |
| 1LMB | REFINED 1.8 ANGSTROM CRYSTAL STRUCTURE OF THE LAMBDA REPRESSOR-OPERATOR COMPLEX | X-ray 1.80 Å | 1991-11-05 | 2334 | yes | held back | 12 |
| 1LYZ | Real-space refinement of the structure of hen egg-white lysozyme | X-ray 2.00 Å | 1975-02-01 | 1102 | yes | public | 3 |
| 1MBN | The stereochemistry of the protein myoglobin | X-ray 2.00 Å | 1973-04-05 | 1260 | yes | public | 10 |
| 1PLC | ACCURACY AND PRECISION IN PROTEIN CRYSTAL STRUCTURE ANALYSIS: RESTRAINED LEAST-SQUARES… | X-ray 1.33 Å | 1992-03-11 | 1657 | yes | public | 5 |
| 1RX2 | DIHYDROFOLATE REDUCTASE (E.C.1.5.1.3) COMPLEXED WITH WITH FOLATE AND NICOTINAMIDE ADENI… | X-ray 1.80 Å | 1996-09-19 | 1503 | no | held back | 16 |
| 1STP | STRUCTURAL ORIGINS OF HIGH-AFFINITY BIOTIN BINDING TO STREPTAVIDIN | X-ray 2.60 Å | 1992-03-12 | 1001 | yes | public | 10 |
| 1TRN | CRYSTAL STRUCTURE OF HUMAN TRYPSIN 1: UNEXPECTED PHOSPHORYLATION OF TYROSINE 151 | X-ray 2.20 Å | 1995-03-16 | 3705 | yes | public | 18 |
| 1TUP | TUMOR SUPPRESSOR P53 COMPLEXED WITH DNA | X-ray 2.20 Å | 1995-07-11 | 5828 | no | public | 16 |
| 1UBQ | STRUCTURE OF UBIQUITIN REFINED AT 1.8 ANGSTROMS RESOLUTION | X-ray 1.80 Å | 1987-01-02 | 660 | yes | public | 2 |
| 1UDT | Crystal structure of Human Phosphodiesterase 5 complexed with Sildenafil(Viagra) | X-ray 2.30 Å | 2003-05-06 | 2655 | no | public | 12 |
| 1Y26 | A-riboswitch-adenine complex | X-ray 2.10 Å | 2004-11-20 | 1608 | – | public | 9 |
| 2C9V | Atomic resolution structure of Cu-Zn Human Superoxide dismutase | X-ray 1.07 Å | 2005-12-14 | 3043 | yes | held back | 18 |
| 2CPP | HIGH-RESOLUTION CRYSTAL STRUCTURE OF CYTOCHROME P450-CAM | X-ray 1.63 Å | 1987-04-06 | 3462 | yes | public | 13 |
| 2HHB | THE CRYSTAL STRUCTURE OF HUMAN DEOXYHAEMOGLOBIN AT 1.74 ANGSTROMS RESOLUTION | X-ray 1.74 Å | 1984-03-07 | 4779 | yes | public | 22 |
| 2NWD | Structure of chemically synthesized human lysozyme at 1 Angstrom resolution | X-ray 1.04 Å | 2006-11-14 | 2691 | yes | public | 11 |
| 2OMF | OMPF PORIN | X-ray 2.40 Å | 1995-02-28 | 2827 | yes | held back | 6 |
| 2P4E | Crystal Structure of PCSK9 | X-ray 1.98 Å | 2007-03-12 | 4776 | no | public | 10 |
| 2PTC | THE GEOMETRY OF THE REACTIVE SITE AND OF THE PEPTIDE GROUPS IN TRYPSIN, TRYPSINOGEN AND… | X-ray 1.90 Å | 1982-09-27 | 2241 | yes | held back | 12 |
| 3AVE | Crystal Structure of the Fucosylated Fc Fragment from Human Immunoglobulin G1 | X-ray 2.00 Å | 2011-03-04 | 3796 | yes | public | 10 |
| 3EML | The 2.6 A Crystal Structure of a Human A2A Adenosine Receptor bound to ZM241385. | X-ray 2.60 Å | 2008-09-24 | 3757 | yes | public | 11 |
| 3ERT | HUMAN ESTROGEN RECEPTOR ALPHA LIGAND-BINDING DOMAIN IN COMPLEX WITH 4-HYDROXYTAMOXIFEN | X-ray 1.90 Å | 1999-03-30 | 2070 | no | public | 11 |
| 3F9M | Human pancreatic glucokinase in complex with glucose and activator showing a mobile flap | X-ray 1.50 Å | 2008-11-14 | 4065 | no | public | 14 |
| 3K34 | Human carbonic anhydrase II with a sulfonamide inhibitor | X-ray 0.90 Å | 2009-10-01 | 2387 | yes | public | 9 |
| 3KCG | Crystal structure of the antithrombin-factor IXa-pentasaccharide complex | X-ray 1.70 Å | 2009-10-21 | 6669 | yes | held back | 16 |
| 3NGB | Crystal structure of broadly and potently neutralizing antibody VRC01 in complex with H… | X-ray 2.68 Å | 2010-06-11 | 25808 | yes | public | 5 |
| 3PTB | THE GEOMETRY OF THE REACTIVE SITE AND OF THE PEPTIDE GROUPS IN TRYPSIN, TRYPSINOGEN AND… | X-ray 1.70 Å | 1982-09-27 | 1701 | yes | public | 12 |
| 4INS | THE STRUCTURE OF 2ZN PIG INSULIN CRYSTALS AT 1.5 ANGSTROMS RESOLUTION | X-ray 1.50 Å | 1989-07-10 | 1182 | yes | public | 13 |
| 5CJ6 | Crystal Structure of a Selective Androgen Receptor Modulator Bound to the Ligand Bindin… | X-ray 2.07 Å | 2015-07-14 | 2233 | yes | public | 15 |
| 5EDM | Crystal structure of prothrombin deletion mutant residues 154-167 ( Form I ) | X-ray 2.20 Å | 2015-10-21 | 5005 | yes | public | 13 |
| 5NI1 | CryoEM structure of haemoglobin at 3.2 A determined with the Volta phase plate | EM 3.20 Å | 2017-03-22 | 4579 | yes | held back | 15 |
| 5UAK | Dephosphorylated, ATP-free human cystic fibrosis transmembrane conductance regulator (C… | EM 3.87 Å | 2016-12-19 | 9232 | no | public | 8 |
| 6HPO | Crystallographic structure of the catalytic domain of Human Phenylalanine Hydroxylase (… | X-ray 1.67 Å | 2018-09-21 | 2880 | no | held back | 6 |
| 6M7H | Structure of calmodulin with KN93 | X-ray 1.60 Å | 2018-08-20 | 1311 | yes | public | 17 |
| 6TC2 | Monoclinic human insulin in complex with p-coumaric acid | X-ray 1.36 Å | 2019-11-04 | 5094 | yes | held back | 16 |
| 6THA | Crystal structure of human sugar transporter GLUT1 (SLC2A1) in the inward conformation | X-ray 2.40 Å | 2019-11-19 | 3556 | no | held back | 7 |
| 6VXX | Structure of the SARS-CoV-2 spike glycoprotein (closed state) | EM 2.80 Å | 2020-02-25 | 23694 | no | public | 8 |
| 7A4M | Cryo-EM structure of mouse heavy-chain apoferritin at 1.22 A | EM 1.22 Å | 2020-08-20 | 3177 | yes | public | 9 |
| 8C86 | Crystal structure of human transthyretin in complex with 3-O-methyltolcapone analogue 2 | X-ray 1.10 Å | 2023-01-18 | 4150 | yes | public | 22 |
| 8CE0 | N-terminal domain of human apolipoprotein E | X-ray 1.75 Å | 2023-02-01 | 1335 | yes | held back | 12 |
| 8EPH | Crystal structure of human coagulation factor IXa (S195A), apo-form, DES-GLA | X-ray 1.88 Å | 2022-10-05 | 5564 | yes | public | 19 |
| 8K7F | Crystal structure of human lysosomal alpha-galactosidase A in complex with (2R,3S,4R,5R… | X-ray 1.98 Å | 2023-07-26 | 7126 | no | held back | 13 |
| 8PI2 | Native alpha-1-antitrypsin at 1.5 Angstrom (Cys232Ser) | X-ray 1.48 Å | 2023-06-20 | 6156 | yes | public | 10 |
| 9F69 | Crystal structure of human triose phosphate isomerase with methyl malonic acid ligand | X-ray 1.17 Å | 2024-04-30 | 4040 | no | public | 10 |
| 9FB2 | Gcase in complex with small molecule inhibitor 1 | X-ray 1.14 Å | 2024-05-11 | 4971 | no | public | 15 |
| 9GIO | Crystal structure of the VHL-EloC-EloB complex with a covalent compound bound to C77 of… | X-ray 1.49 Å | 2024-08-19 | 3043 | no | public | 15 |
| af-p04637-f1-model_v6 | AlphaFold DB model of Cellular tumor antigen p53 (TP53, Homo sapiens) | AlphaFold prediction | 2025-08-01 | 3060 | no | public | 5 |
| af-p07320-f1-model_v6 | AlphaFold DB model of Gamma-crystallin D (CRYGD, Homo sapiens) | AlphaFold prediction | 2025-08-01 | 1459 | no | public | 3 |
| af-p0dp23-f1-model_v6 | AlphaFold DB model of Calmodulin-1 (CALM1, Homo sapiens) | AlphaFold prediction | 2025-08-01 | 1174 | no | public | 3 |
| af-p61626-f1-model_v6 | AlphaFold DB model of Lysozyme C (LYZ, Homo sapiens) | AlphaFold prediction | 2025-08-01 | 1157 | no | public | 2 |
| af-p68871-f1-model_v6 | AlphaFold DB model of Hemoglobin subunit beta (HBB, Homo sapiens) | AlphaFold prediction | 2025-08-01 | 1131 | no | public | 10 |

### S3.2 The variant list, step by step

We use *missense* variants only: one amino acid replaced by another. Throughout, the
*classification* of a variant means ClinVar's aggregate germline classification on a variation
record, the record whose accession begins with VCV. ClinVar keeps germline classifications
(of inherited variants) apart from somatic ones; we use the germline one. A variation record
is usually about one change at the level of DNA, and different DNA changes can give the same
amino-acid change, so one amino-acid change can have several records.
74 of the variants that we keep have more than one qualifying
record.

**Table S4. The variant list in three steps.** Counts are of variants (amino-acid changes)
removed and left. The tests 3a to 3c are applied in this order. Section 3.1 of the paper uses
the same step numbers and gives step 3 as one step.

| Step | Rule | Removed | Left |
|:--|:----------------------------------|---:|---:|
| 1 | Single-residue missense variants of the 27 proteins that UniProt reports as pathogenic or likely pathogenic, with ClinVar as a source | | 3,352 |
| 2 | Keep if a ClinVar variation record, reached through UniProt's cross-references, lists the same amino-acid change at that position and has the aggregate germline classification "Pathogenic", "Likely pathogenic" or "Pathogenic/Likely pathogenic" (a *qualifying record*) | 657 | 2,695 |
| 3a | Remove if no qualifying record is of the gene that the request names | 44 | |
| 3b | Remove if every qualifying record of that gene is a haplotype (two changes on one chromosome) | 35 | |
| 3c | Remove if every remaining qualifying record has the review status "no assertion criteria provided" | 216 | 2,400 |

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
change of a record for each transcript; we did not check which transcript the matching name
belongs to. We therefore rely on at least one reference protein of the record being numbered as
the UniProt canonical sequence is at that position. We also did not look for further records
of the same amino-acid change that carry another classification: one qualifying record is
enough, and ClinVar may hold a second record that disagrees with it.

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
lysozyme amyloidosis [1]. It is outside the 2,400. Its
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
harmonic mean. How much of a fact the other side has:

- *Fact about atoms*: the mean over its atoms of the share of the atom's styles that the other side
  also has. A style that the other side has with the same representation type and another
  colour or opacity counts half. An atom that the other side does not draw counts 0. Styles that
  the other side has in addition do not lower this number; they lower the number computed in
  the other direction.
- *Label, tooltip, interaction request*: the share of the atoms carrying it that carry the
  same on the other side.
- *Camera target*: the overlap (intersection over union) of the two targets, as whole
  residues.
- *Primitive, structure type, background*: 1 if the other side has the same, else 0.

An answer that draws nothing scores 0 on every score when the reference draws something.

### S4.3 Target score

The *target's drawing* is the set of the reference's styles that lie wholly inside the target
atoms (in the running example the yellow spacefill spheres of the residue; a cartoon of the
whole chain that passes through the residue is not part of it). It is
cut into facts as above. For each fact, counting (atom, style) items:

- *wanted*: the reference's items;
- *credit*: 1 for each item the answer has, ½ for each that the answer draws in the right
  representation with another colour or opacity;
- *attempted*: the items the answer drew at all;
- *spill*: items outside the target on which the answer repeats a style that it drew on the
  target and that earned credit there (the requested representation, in the requested colour
  or in another), where the reference draws no such thing;
- *extra*: items on the target from a style of the answer that is confined to the target, in
  a representation type that the reference does not draw there.

Target recall = credit / wanted. Target precision = credit / (attempted + spill + extra). The
target score is the harmonic mean of the two, each averaged over the target's facts and over
the facts about the scene that touch the target atoms. The three rules for extra drawing follow from these counts. *Spill*: the answer repeats, on
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
Rows S9 and S10 of Table S1 show the two cases side by side.

Tasks without a stored target are of two kinds (Section 4.2 of the paper). A single request
without one, such as a change of the background colour, uses everything the reference draws or
changes as its target. A follow-up task without one, in which the edit takes something away
or resets a setting, has no target score, and averages leave it out: there are no atoms
"drawn as asked", and to use everything the reference draws would give full marks to the
start state returned unchanged.

### S4.4 Accepted answers and follow-up turns

A task may list further right answers. An answer is graded against the reference and each of
them, and the best result counts (a success first, then the highest F1). A name-resolution
task lists the entries that match the named protein. The list was frozen on
13 November 2026 from the web services of the RCSB PDB (the US member site of the
Protein Data Bank): it holds every current PDB entry
in which a chain is aligned to the UniProt accession of the named protein over at least
50 residues in total, or over at least half of the UniProt sequence if
that is shorter. Where the request names several proteins, a ligand or bound DNA, the entry
must hold all of them. An answer on another listed entry is graded against the reference's
drawing resolved on that entry; where that entry is outside the structure panel, selections
are compared as written (Section S4.8), and F1, task success and the target score all come
from that comparison. A follow-up task gives a start
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
- Two representations on overlapping components are both drawn; the atom carries both styles.
- Author and label numbering are different columns and are never pooled.
- A reference that colours "by chain" is matched by the same colour theme, or by an answer
  that gives every chain one colour of its own, all different.

Not graded on the scene track: metadata, the host of the structure file, the order of
children, representation size and surface kind, the appearance of labels and primitives, explicit camera
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
from the scene track. A fact about atoms scores the share of its atoms that end up looking exactly
the same on the other side; atoms that both sides changed but that look different count half.
The target score is computed on the changes from a bare load on the target atoms. Selections in
UniProt numbering are resolved through the frozen SIFTS tables; the viewer reads the same
mapping from the structure file that PDBe distributes.

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
- **Call-list track.** Options that need live services (superposition, ligand view,
  annotations, density maps, lighting) are compared as declared settings. Camera focus,
  highlight and UniProt-numbered selections were not read back from the viewer. Which atoms
  are polymer, ligand, ion or water comes from tables filled by Mol\* 5.9.0, whereas PDBe Mol\*
  3.3.2 carries an older Mol\*; a bare load of 73 entries was
  compared with the viewer, and the two differences found are modelled as measured.
- **A second cartoon.** An answer that recolours a stretch by adding a second coloured cartoon
  over the first draws two cartoons there and fails task success.

## S5. The control set by kind

The control set has 2,105 controls on the structures of the structure panel, each a reference
and one answer: 1,110 on the scene track (150
identical, 480 equivalent, 480 wrong) and
995 on the call-list track (150 identical,
425 equivalent, 420 wrong). The verdict of each
control is known from how its answer was made.

Read-back from the viewers. Scene track: the read-back was run on the control set as it then
stood, 1,030 scene controls. For
890 of them both scenes were loaded in Mol\*
5.9.0 and their drawing read back; in all of them the viewer agreed with
the verdict. The other 140 are of kinds that cannot be read back
(camera target, label text, colouring by chain, assembly, another entry).
80 scene controls were added afterwards and have not been
read back in the viewer. In the same run the grader's resolved state equalled the viewer's for all
1,498 scenes, and 3,818 single
representations probed across the panel were drawn as the grader predicts. Call-list track:
the replay was run on the control set as it then stood,
850 call-list controls of 36
kinds. A sample of 120 controls was drawn by taking one control
from each kind in turn, and again, until that number was reached. Each control has two call
lists, its reference and its answer, so the sample holds
240. The 3 that select
by UniProt number were left out, and 3 could not be run by
our replay script. The other 234 call lists were replayed in PDBe
Mol\* 3.3.2, and every one ended in the state that the grader
computes. 145 call-list controls were added afterwards. The
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
| must pass (equivalent) | the entry id in upper case, or the same entry loaded by URL | 20 | 20 | 7 |
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
| must pass (identical) | the answer is the reference itself | 150 | 150 | 150 |
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
| must fail (wrong) | the same residue number in another chain | 20 | 0 | 0 |
| must fail (wrong) | another palette colour | 20 | 0 | 0 |
| must fail (wrong) | the same calls on another structure | 20 | 0 | 0 |
| must fail (wrong) | another copy of the ligand than the one asked for | 20 | 0 | 0 |
| must fail (wrong) | another representation type for the residue | 20 | 0 | 0 |

## S6. The run manifest

The final run is defined by one manifest file in the repository. Its contents, in words:

- **Corpus.** Version `corpus-v1.0-dev` ⟦PENDING: corpus freeze — final version tag and hash⟧.
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

## S7. System prompts

The two system prompts as sent in the main condition, and then the texts that fill their
slots. A name in double angle brackets, such as `<<MVS_REFERENCE>>`, marks a slot that is
filled with a longer frozen text. These longer texts are the *format guide* of each track:
for the scene track the MolViewSpec reference; for the call-list track the list of actions
with their fields, followed by the reference of the viewer's calls. With its slots filled,
the system prompt has 1,216 words on the scene track and
1,514 on the call-list track. In the condition without a format guide, the
section "MVS reference" is removed. Each prompt has one worked example, on entry 1HSG, which
no task uses: the example of the call-list prompt is in the prompt itself, and that of the
scene prompt sits inside its format guide. The format guide of the scene track also has one
short illustration of a distance line on entry 1A6M, which tasks use; no task asks for that
distance.

The prompts and guides are printed as sent, so they use the words of the repository and not
those of the paper. In them, *MVS* is MolViewSpec, an *MVS state* or *scene tree* is a scene,
an *action* (or *canonical action*) is one call of a call list, and *pdbe-molstar* is PDBe
Mol\*.

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

**Scene track: the format guide** (slot `<<MVS_REFERENCE>>`), 975 words.

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
(`"#FF6699"`). A `color` node takes ONE colour.

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

**Call-list track: the format guide, second part (the reference of the viewer's calls)** (slot `<<API_REFERENCE>>`), 983 words.

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
| `molecule_id` | str | PDB id, e.g. `"1cbs"`. With `superposition=True` it is a **UniProt accession** instead. |
| `custom_data` | dict | `{"url": str, "format": "cif"\|"bcif"\|"pdb", "binary": bool}` — load any structure file by URL instead of a PDB id. An AlphaFold DB model is `https://alphafold.ebi.ac.uk/files/AF-<accession>-F1-model_v6.cif`. |
| `assembly_id` | str | Biological assembly to build, e.g. `"1"`; `"preferred"` = the first. Default: the deposited model. |
| `default_preset` | enum | `default` \| `unitcell` \| `all-models` \| `supercell`. |
| `ligand_view` | dict | PDBe ligand page view: only that ligand and its surroundings. `{"label_comp_id": "REA"}` and/or `auth_asym_id` + `auth_seq_id`. |
| `alphafold_view` | bool | Colour by AlphaFold confidence (pLDDT). It does **not** load a model: load one with `custom_data`. |
| `superposition` | bool | PDBe-KB superposition view: the superposed PDB entries of one protein, addressed by UniProt accession in `molecule_id`. |
| `superposition_params` | dict | `{"matrixAccession": str, "segment": int, "cluster": [int], "superposeCompleteCluster": bool, "ligandView": bool, "superposeAll": bool, "ligandColor": color}`. |
| `visual_style` | enum | One representation for every component: `cartoon`, `ball-and-stick`, `carbohydrate`, `ellipsoid`, `gaussian-surface`, `molecular-surface`, `point`, `putty`, `spacefill`. Unset = the default view: polymer as cartoon; ligands, ions, waters and non-standard residues as ball-and-stick. `cartoon` and `putty` draw polymer only (ligands, ions and waters disappear). |
| `hide_polymer`, `hide_water`, `hide_heteroatoms`, `hide_carbs`, `hide_non_standard`, `hide_coarse` | bool | Hide the polymer / waters / ligands and ions / carbohydrates / non-standard residues / coarse parts. |
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

**Table S8. Corpus of the October 2026 pilot run (pilot run, preliminary, earlier grader).** Tasks and distinct structures (PDB entries) per category. A category is a group of tasks that need the same kind of knowledge.

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

⟦PENDING: final run — the tables that Section 6.5 of the paper points to, for both tracks: outcome counts per model (valid, unshowable by kind, schema-breaking, cut off), the JSON-repair counterfactual, F1 valid-only, cost per model, and the one-sided pairs of Table 9 divided by whether the side that was not right was unshowable⟧

## References

1. Pepys MB, Hawkins PN, Booth DR, Vigushin DM, Tennent GA, Soutar AK, Totty N, Nguyen O et al. Human lysozyme gene mutations cause hereditary systemic amyloidosis. *Nature* 1993;362(6420):553–557. doi:[10.1038/362553a0](https://doi.org/10.1038/362553a0)
