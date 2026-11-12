# The structure panel

The structures the benchmark's tasks are built on, and everything frozen about them.
Task generators read this directory (through `molbench.grounding`) and never the
network; graders read only `molbench/atom_tables/` and `molbench/sifts_tables/`.

- **`PANEL.md`** — the panel as a table (generated; start here).
- **`seed.json`** — the hand-written input: named entries with the features we claim
  for them, disease proteins by UniProt accession, AlphaFold accessions.
- **`panel.json`** — one record per entry: why it is here, what the file shows
  (`features`), the task families it can serve (`families`), size, method, source URL,
  retrieval date, SHA-256 of the structure file; plus the disease-protein table.
- **`cif/<id>.cif.gz`** — the exact structure file everything else was derived from
  (RCSB mmCIF; AlphaFold DB mmCIF for `af-…` ids).
- **`facts/<id>.json`** — grounding facts extracted from that file.
- **`variants/<ACCESSION>.json`** — pathogenic ClinVar missense variants per disease
  protein, mapped to the panel structures.
- `molbench/atom_tables/<id>.json.gz` and `molbench/sifts_tables/<id>.json.gz` live in
  the package because grading needs them.

Rebuild: `uv run --all-extras python scripts/build_panel.py` (frozen-first: no network,
no change, unless `seed.json` changed or `--refresh` is given), then
`uv run --all-extras python scripts/build_atom_tables.py --panel` (needs
`scripts/fetch_molstar.py` and `playwright install chromium`).

## The selection rule (`panel-v1`)

The panel is the union of four groups. Rules 1–3 apply to every entry.

1. **Current.** The entry's RCSB holdings status is `CURRENT` (not obsolete).
2. **Modest size.** At most 15,000 atoms in the first model, so rendering is fast.
   The only exemption is an entry an existing task already uses (3NGB, 6VXX); they
   are flagged `over_size_limit`.
3. **Claims are verified.** Every feature claimed in `seed.json` must be found in
   the file by the build, or the build fails. Verified features are recorded for
   every entry whether claimed or not. How each is read:
   `ligand` a non-polymer group with more than one heavy atom · `heme` a heme
   component · `metal` a metal atom in a non-polymer group · `disulfide` a `disulf`
   record in `_struct_conn` · `nucleic` a DNA or RNA polymer · `protein-dna` both ·
   `glycan` a branched (oligosaccharide) entity · `assembly-differs` assembly 1 is
   built with symmetry operators or uses only part of the deposited chains ·
   `insertion-codes`, `auth-label-chain`, `auth-label-number` from `_atom_site` ·
   `uniprot-offset` an observed residue whose author number is not its UniProt
   number (SIFTS) · `modified-residue` a non-standard residue inside a polymer (not `UNK`, the
   placeholder for an unidentified residue) ·
   `membrane` listed by PDBTM or mpstruc (via RCSB annotations) · `cryo-em`, `nmr`
   the experimental method · `clinical` at least one verified variant (below).

**Group A — entries tasks already use.** Every structure loaded by a task in
`tasks/**` (MVS downloads and call-list `molecule_id`s). The build fails if one is
missing from `seed.json`. 22 PDB entries and one AlphaFold model.

**Group B — named entries.** Hand-picked to cover what group A lacks: small and
large folds, more protein–ligand complexes, hemes and metal sites, disulfide-rich
proteins, RNA, DNA and protein–DNA complexes, assemblies that differ from the
deposited model, glycans, membrane proteins, cryo-EM and NMR entries. Preference:
well-known entries, X-ray at 2.5 Å or better where one exists. The choice is by hand
(a search rule would pick obscure entries that no closed-book model could name); the
check is by script (rule 3).

**Group C — disease proteins.** `seed.json` lists human proteins by UniProt
accession. For each, the pathogenic variants are fetched first (next section), then
the structure is chosen by script:

1. Candidates: every PDB entry SIFTS maps to the accession (PDBe `best_structures`).
2. Keep X-ray entries at 2.5 Å or better that cover at least one variant position.
   (If none: X-ray or cryo-EM at 3.5 Å or better.)
3. Shortlist the 30 that cover the most variant positions (ties: better resolution).
4. Drop entries over 15,000 atoms or with more than one model.
5. Choose by, in order: most variant positions covered · fewest engineered
   mutations (RCSB mutation count) · fewest polymer entities · best resolution · id.

A protein whose structure is already used by tasks keeps that entry (`"entry"` in
`seed.json`: TP53 → 1TUP, HBA1/HBB → 2HHB, CFTR → 5UAK). The rule's audit trail
(candidates, shortlist, runner-up) is stored per protein in `panel.json`. Whether a
protein's author numbering differs from UniProt was **not** used to choose: the
offsets are whatever the chosen structures have.

**Group D — AlphaFold models.** The current AlphaFold DB model of the accessions in
`seed.json`: p53 (an existing task loads it) and haemoglobin β (the same protein as
2HHB chain B, but numbered as UniProt). Ids are the lower-cased file name
(`af-p04637-f1-model_v6`), which is also what the MVS grader derives from a download
URL.

## Clinical variants (`variants/<ACCESSION>.json`)

Two sources, both recorded with URL and retrieval date.

1. **Candidates** from the UniProt Proteins Variation API,
   `https://www.ebi.ac.uk/proteins/api/variation/<accession>` (`source`, `retrieved`):
   a single-residue `VARIANT` feature with `consequenceType` missense, clinical
   significance *Pathogenic* or *Likely pathogenic* **with ClinVar named as a source
   of that call**, a ClinVar cross-reference, and a wild type equal to the UniProt
   canonical residue at that position. Duplicated features are merged.
2. **Confirmation** from ClinVar itself, through NCBI E-utilities (`clinvar_source`,
   `clinvar_retrieved`). UniProt reports a variant as pathogenic when any one ClinVar
   submission says so; ClinVar's own verdict is the aggregate over all submitters,
   and for about one candidate in five it is "Conflicting classifications of
   pathogenicity" or "Uncertain significance". A candidate is kept only if a ClinVar
   variant record (VCV) reached through its cross-references names the same protein
   change and has the aggregate germline classification *Pathogenic*, *Likely
   pathogenic* or *Pathogenic/Likely pathogenic* (a trailing qualifier such as
   "; other" or "; drug response" is allowed).

Everything else is listed under `rejected` with the reason and, for step 2, the
classification ClinVar gives. Disease-protein structures (group C) were ranked on the
candidate positions of step 1.

Per variant: `variant` (e.g. `E7V`), `position`, `wild_type`, `mutant`, `significance`
(UniProt's), `clinvar_vcv`, `clinvar_classification` and `clinvar_review_status` (the
confirming ClinVar records; `https://www.ncbi.nlm.nih.gov/clinvar/variation/<VCV>`),
`clinvar` (their RCV accessions; `https://www.ncbi.nlm.nih.gov/clinvar/<RCV>`), `dbsnp`,
`diseases`, and `structures`: for each panel entry holding the protein, the residues
the position maps to (author chain, number and insertion code; label chain and
number; residue name).

**Identity check.** A residue is listed only if the structure has the wild-type amino
acid there. If the structure has something else (an engineered or natural
substitution), the residue is left out and recorded under `structure_mismatches`; a
variant with no matching residue in an entry is simply not offered for that entry.
`entries.<id>` counts, per entry, how many variants were `verified`,
`not_observed` (in the construct, not modelled), `outside_construct`, or
`wild_type_mismatch`, and gives that entry's author-minus-UniProt offsets.

`pathogenic_single_residue_variants_per_position` counts every single-residue variant
UniProt reports as pathogenic with ClinVar as a source (not only missense, and
**before** the ClinVar confirmation of step 2) per UniProt position. For a "hotspot"
count that matches the confirmed list, count `variants` by `position` instead.

## SIFTS tables (`molbench/sifts_tables/<id>.json.gz`)

One row per residue mapped to a UniProt position: accession, UniProt number and
residue, label chain and number, author chain, number and insertion code, the residue
in the structure, and whether it is observed. Observed rows are read from
`_atom_site.pdbx_sifts_xref_db_*` of PDBe's SIFTS-annotated ("updated") mmCIF
(`https://www.ebi.ac.uk/pdbe/entry-files/download/<id>_updated.cif`), taking each
residue's first atom — the columns Mol\* reads for its SIFTS mapping, which is what the
PDBe viewer's `uniprot_accession` / `uniprot_residue_number` selections resolve
against. Unobserved rows come from `_pdbx_sifts_xref_db` and `_pdbx_poly_seq_scheme`.
The build fails if the residues of the SIFTS file and of the frozen RCSB file are not
identical, one for one. AlphaFold models carry the same columns and get the same
treatment. Entries with no UniProt mapping (DNA, RNA, a designed peptide) have no
table; `panel.json` says so (`"sifts": false`).

Read them with `molbench.sifts`: `uniprot_residues(entry, accession, n)`,
`uniprot_atoms(entry, accession, n[, end])` (atoms as a bitmask over the atom table),
and the older `mappings(entry)` / `unp_to_auth(...)` segment interface. None of these
use the network; `mappings(entry, allow_network=True)` is the only path that can, and
only for an entry without a table.

Known quirk: the accession is stored exactly as the file gives it. One entry, 3AVE,
is mapped to the isoform accession `P01857-1`, so `P01857` finds nothing there —
exactly as in the viewer.

## Facts (`facts/<id>.json`)

Everything is from the frozen mmCIF, first model, plus the SIFTS table.

| field | content |
|---|---|
| `title`, `method`, `resolution`, `n_models`, `n_atoms`, `n_residues`, `waters` | as deposited |
| `entities` | id, type, polymer type, description, label chain ids |
| `chains` | per polymer chain: author and label chain id, entity, SEQRES length, observed residues, `runs_auth_label` (`[auth first, auth last, label first, label last]`), `auth_minus_label` (offset → residue count), insertion-code count, and `uniprot`: per accession the observed UniProt range, `auth_minus_unp` (offset → residue count), `same_numbering`, `runs_auth_unp` |
| `ligands` | per component: name, formula, `kind` (`ligand`, `ion`, `sugar`), metals, `heme`, heavy-atom names, every copy (author and label position) |
| `disulfides`, `metal_bonds`, `covalent_links` | `_struct_conn` records: both ends (chain, number, residue, atom), distance, `to_symmetry_copy` |
| `glycans` | per branched chain: its sugars and the residue it is attached to |
| `glycosylation_sites` | every polymer residue with a sugar bonded to it (branched or single) |
| `modified_residues` | non-standard residues inside polymer chains (selenomethionine counts; `UNK` placeholders do not) |
| `assemblies` | id, description, oligomeric count, copies of each polymer chain, `relation_to_deposited` (`same as deposited`, `part of deposited`, `built by symmetry`) |
| `helices`, `strands` | as annotated in the file (author and label ranges) |
| `numbering` | four flags: author chain ≠ label chain, author number ≠ label number, insertion codes, author number ≠ UniProt number |
| `plddt` | AlphaFold models only: per-residue confidence and its mean |

## Checks made when this was built (2026-11-12)

- Atom tables: every static selector and 21–30 probe selections per entry agree
  with headless Mol\* 5.9.0 (`scripts/build_atom_tables.py`).
- SIFTS tables against the PDBe mappings API (segment end points, author numbering):
  187 of 187 agree. Against RCSB's SIFTS alignments (label numbering): 69 of 74
  entries identical; the other five are constructs with an internal deletion or a
  merged chromophore (1C3W, 1D5R, 1EMA, 5EDM) where RCSB reports one unbroken region
  and the residue identities show the PDBe mapping is the right one, and 3AVE
  (isoform accession, above).
- The tests in `tests/test_panel.py` and `tests/test_sifts_frozen.py` re-check the
  frozen files against each other and against residue numbers known from the
  literature, with the network blocked.
- Independent review (2026-11-12): all 30,310 rows of the SIFTS tables name the
  residue that the current UniProt sequence has at that position; every atom-table
  column equals the frozen mmCIF read afresh, for all 76 entries; the variant lists
  were rebuilt independently from the raw UniProt responses; a sample of ten variants
  looked up in ClinVar found three that ClinVar calls "Conflicting", which is why
  step 2 of the variant rule exists (it removed 657 of 3,352 candidates).
