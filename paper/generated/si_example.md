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

**Call-list track: accepted alternative** (the residue's own cartoon stretch is painted green as well).

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
