## S3. The structure panel

**Selection rule.** The panel is the union of four groups. Every entry must be current in the
PDB archive and have at most {{panel.max_atoms:,}} atoms in its first model
({{panel.n_over_size_limit}} larger entries are kept because earlier tasks used them). Every
feature claimed for an entry (ligand, haem, metal, disulfide, nucleic acid, glycan, membrane
protein, assembly that differs from the deposited model, insertion codes, author chain
identifiers that differ from label identifiers, a UniProt numbering offset) must be found in the
file by the build script, or the build fails.

1. *Entries used by earlier tasks.*
2. *Named entries*, chosen by hand to cover folds and features that the first group lacks.
   Well-known entries were preferred, solved by X-ray crystallography at 2.5 Å or better where
   one exists. The choice is by hand; the check of each claimed feature is by script.
3. *Disease proteins.* {{panel.n_disease_proteins}} human proteins are listed by UniProt
   accession. For each, candidate entries are all PDB entries that SIFTS maps to the accession.
   The script keeps X-ray entries at 2.5 Å or better that cover at least one variant position
   (failing that, X-ray or cryo-electron microscopy entries at 3.5 Å or better), drops entries
   above the size limit or with several models, and then chooses by, in order: most variant
   positions covered, fewest engineered mutations, fewest polymer entities, best resolution.
   Whether the author numbering differs from UniProt was not a criterion.
4. *Two AlphaFold models*, numbered as UniProt is by construction: one of p53 and one of
   haemoglobin β, the latter as a partner to a crystal structure of the same protein that is
   numbered differently.

Counts of verified features in the panel: ligand {{panel.feature.ligand}}, metal
{{panel.feature.metal}}, disulfide {{panel.feature.disulfide}}, assembly differs
{{panel.feature.assembly-differs}}, author chain identifier differs from label identifier
{{panel.feature.auth-label-chain}}, glycan {{panel.feature.glycan}}, nucleic acid
{{panel.feature.nucleic}}, modified residue {{panel.feature.modified-residue}}, haem
{{panel.feature.heme}}, insertion codes {{panel.feature.insertion-codes}}, membrane protein
{{panel.feature.membrane}}. Structure files were retrieved on {{panel.retrieved}}; the
checksum of each file is stored with the panel.

**Table S3. The panel.** *Atoms*: atoms in the first model. *Author numbering differs from
UniProt*: at least one observed residue has an author number that is not its UniProt position
(a dash: no protein chain mapped to UniProt). *Split*: public, or held back (structures used
only by held-back tasks). *Tasks*: tasks of the corpus on this structure, both tracks, without
rephrasings.

{{include:generated/si_panel.md}}
