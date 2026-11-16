| Step | Rule | Removed | Left |
|:---|:---|---:|---:|
| 1 | Single-residue missense variants of the 27 proteins that UniProt reports as pathogenic or likely pathogenic, with ClinVar as a source | | 3,352 |
| 2 | Keep if a ClinVar variation record lists the same amino-acid change and its aggregate classification is pathogenic, likely pathogenic or both | 657 | 2,695 |
| 3a | Remove if the only such record belongs to another gene | 44 | |
| 3b | Remove if the only such record is a haplotype (two changes on one chromosome) | 35 | |
| 3c | Remove if every such record has the review status "no assertion criteria provided" | 216 | 2,400 |
