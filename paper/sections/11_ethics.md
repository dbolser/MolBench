## 11. Ethics, human participants and licences

**No patient data.** The benchmark contains no data about individuals. Clinical variants come
from UniProt's variant annotation and are confirmed in ClinVar's public variant-level
records; no individual-level data are used. A variant
serves only as a residue position with a classification label.

**Not for clinical use.** A high score does not make a model fit to interpret variants. The
clinical category measures whether a model can locate a residue in a structure. The data providers
say the same of their data: UniProt and the AlphaFold Protein Structure Database state that
their content is not a substitute for professional medical advice. ⟦PENDING: Dan — ClinVar's own statement on clinical use, to be read at the source by hand and added to this sentence; the page refuses automated reading⟧

**Volunteer raters.** The rating study asks volunteers to compare pictures of a molecule,
a reference and a model answer at a time. It collects their answers, optional free-text notes
and the time taken per item. Raters are identified in the analysis by pseudonyms; no names,
contact details or rater identifiers are published. ⟦PENDING: Dan — confirm the consent wording shown to raters, and whether the target journal or the author's institution requires an ethics statement or a waiver for this study⟧

**Use of language models in this work.** Language models are the subject of the study. They
were also used as coding and drafting assistants in building the benchmark and in writing
this manuscript. The authors checked all content and are responsible for it.
⟦PENDING: Dan — final wording of this disclosure, which the journal asks for in the Acknowledgements⟧

**Licences of data and software.** We read each licence at its source on 16 November 2026 (Table
16). Frozen copies of third-party data in the repository keep their original terms and are
attributed in the repository.

**Table 16. Data and software used, with licence or terms as stated at the source.**

| Resource | Used for | Licence or terms | Read at |
|:---|:---|:---|:---|
| Protein Data Bank archive and RCSB PDB web services [@wwpdb2019] | structure files, atom tables, entry annotations | CC0 1.0 public-domain dedication | rcsb.org/pages/usage-policy |
| PDBe: SIFTS mapping, updated structure files, search of entries per protein [@dana2019sifts; @pdbekb2022] | residue mapping, choice of structures | EMBL-EBI terms of use: no additional restrictions on use or redistribution; attribution expected | ebi.ac.uk/about/terms-of-use |
| UniProt [@uniprot2025] | sequences, candidate variants | CC BY 4.0 | uniprot.org/help/license |
| ClinVar [@landrum2018clinvar] | classification of variants | NCBI molecular data policy: NCBI places no restrictions on use or distribution; submitters may hold rights | ncbi.nlm.nih.gov/home/about/policies |
| AlphaFold Protein Structure Database [@varadi2024afdb; @jumper2021alphafold] | {{panel.n_alphafold}} predicted structures | CC BY 4.0 | alphafold.ebi.ac.uk (licence and disclaimer) |
| Mol\* [@sehnal2021molstar] and MolViewSpec [@midlik2025mvs] | scene format, validation, read-back, pictures | MIT | github.com/molstar |
| PDBe Mol\* [@pdbemolstar] | viewer of the call-list track | Apache-2.0 | github.com/molstar/pdbe-molstar |
| ipymolstar [@ipymolstar] | Python host of that viewer | MIT | pypi.org/project/ipymolstar |
| GEMMI [@wojdyr2022gemmi] | reading structure files | MPL-2.0 | github.com/project-gemmi/gemmi |
| json-repair [@jsonrepair] | repair counterfactual | MIT | github.com/mangiucugna/json_repair |

MolBench's own code, tasks and references are released under the MIT licence.
