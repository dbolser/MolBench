## 9. Ethics and data licences

**No human subjects data.** The benchmark contains no patient data. Clinical variants are taken
from public, aggregate variant records and are used only as residue positions with a
significance label.

**Not for clinical use.** A high score does not make a model fit to interpret variants. The
clinical tier measures whether a model can locate a residue in a structure. It does not measure
any judgement about disease.

**Human raters.** The rating study asked volunteers to compare pairs of images.
⟦PENDING: Dan — what was collected from raters, consent wording, and whether an ethics statement
is required by the target journal⟧

**Use of language models in this work.** Language models are the subject of the study. They
were also used as coding and drafting assistants in building the benchmark and this manuscript;
the authors checked and are responsible for all content. ⟦PENDING: Dan — final wording of the
CI-use disclosure, as the target journal requires⟧

**Licences of the data and software used.** ⟦PENDING: confirm each licence statement below
against the provider's current terms page before submission⟧

| Resource | Used for | Licence or terms |
|:---|:---|:---|
| Protein Data Bank structures [@wwpdb2019] | atom tables, references | CC0 1.0 (public domain dedication) |
| SIFTS / PDBe-KB [@dana2019sifts; @pdbekb2022] | UniProt-to-structure residue mapping | CC BY 4.0 (EMBL-EBI) |
| UniProt [@uniprot2025] | sequences, variant records | CC BY 4.0 |
| ClinVar [@landrum2018clinvar] | clinical significance of variants | public domain (NCBI) |
| AlphaFold DB [@varadi2024afdb] | predicted models, where used | CC BY 4.0 |
| Mol\* [@sehnal2021molstar] and MolViewSpec [@midlik2025mvs] | rendering, validation, scene format | MIT |
| pdbe-molstar [@pdbemolstar] | API-track target | Apache-2.0 |
| ipymolstar [@ipymolstar] | API-track call surface | MIT |
| GEMMI [@wojdyr2022gemmi] | reading structure files | MPL-2.0 |

MolBench's own code, tasks and references are released under the MIT licence. Frozen copies of
third-party data in the repository keep their original licences, with attribution.
