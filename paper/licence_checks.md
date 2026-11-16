# Licences — what was verified, and how (2026-11-16)

Each row of Table 12 of the paper was read at its source on 2026-11-16.

| Resource | Source read | What it says | How it was read |
|---|---|---|---|
| PDB archive | <https://www.rcsb.org/pages/usage-policy> | "data files contained in the PDB archive are available under the CC0 1.0 Universal (CC0 1.0) Public Domain Dedication" | page fetched |
| UniProt | <https://rest.uniprot.org/help/license> (the text behind <https://www.uniprot.org/help/license>) | "We have chosen to apply the Creative Commons Attribution 4.0 International (CC BY 4.0) License to all copyrightable parts of our databases." Also: medical information "is not in any way intended to be used as a substitute for professional medical advice" | REST endpoint fetched (the web page needs JavaScript) |
| ClinVar | <https://www.ncbi.nlm.nih.gov/home/about/policies/> ("Molecular Data Usage") | "NCBI itself places no restrictions on the use or distribution of the data contained therein"; "some submitters of the original data ... may claim patent, copyright, or other intellectual property rights" | page fetched |
| AlphaFold DB | <https://alphafold.ebi.ac.uk/assets/License-Disclaimer.pdf> | "Data is available for academic and commercial use, under a CC-BY-4.0 license"; asks for a citation of Jumper et al. 2021; "not intended to be a substitute for professional medical advice" | PDF read |
| PDBe (SIFTS, updated mmCIF, graph API, Proteins API) | <https://www.ebi.ac.uk/about/terms-of-use/> | "EMBL-EBI itself places no additional restrictions on the use or redistribution of the data"; "EMBL-EBI expects attribution" | page fetched |
| Mol\*, MolViewSpec | GitHub API, `molstar/molstar`, `molstar/mol-view-spec` | MIT | `license.spdx_id` |
| pdbe-molstar | GitHub API, `molstar/pdbe-molstar` | Apache-2.0 | `license.spdx_id` |
| ipymolstar | PyPI JSON, `ipymolstar` | MIT (licence text in the package metadata) | `info.license` |
| GEMMI | GitHub API, `project-gemmi/gemmi` | MPL-2.0 | `license.spdx_id` |
| json-repair | GitHub API, `mangiucugna/json_repair` | MIT | `license.spdx_id` |

## Not verified, or changed from the earlier draft

- **ClinVar's own page** (<https://www.ncbi.nlm.nih.gov/clinvar/docs/maintenance_use/>) answered an
  automated fetch with a browser check, so it was **not read**. The paper states NCBI's general
  molecular-data policy, not "public domain". Read the ClinVar page by hand before submission.
- **SIFTS.** The earlier draft and the README said "CC BY 4.0". No page we could fetch states
  a Creative Commons licence for SIFTS; the SIFTS documentation page links to the EMBL-EBI
  terms of use. The paper and the README now cite those terms.
- **Membrane-protein flags** of the panel come from RCSB annotations that RCSB integrates from
  PDBTM and mpstruc. They are used only as a yes/no feature of 7 panel entries; the terms of
  those two resources were not read.
- The licences of the model weights (open / closed in the tables) are taken from the run
  manifest (`open_weights`: the listing names a public weight repository); the individual
  weight licences were not read.
