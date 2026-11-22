| Step | Rule | Removed | Left |
|:---|:---|---:|---:|
| 1 | Single-residue missense variants of the 27 proteins that UniProt reports as pathogenic or likely pathogenic, with ClinVar as a source | | 3,352 |
| 2 | Keep if a ClinVar variation record, reached through UniProt's cross-references, lists the same amino-acid change at that position and has the aggregate germline classification "Pathogenic", "Likely pathogenic" or "Pathogenic/Likely pathogenic" (a *qualifying record*) | 657 | 2,695 |
| 3a | Remove if no qualifying record is of the gene that the request names | 44 | |
| 3b | Remove if every qualifying record of that gene is a haplotype (two changes on one chromosome) | 35 | |
| 3c | Remove if every remaining qualifying record has the review status "no assertion criteria provided" | 216 | 2,400 |
