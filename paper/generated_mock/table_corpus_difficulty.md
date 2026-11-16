**Corpus: difficulty facts under one vocabulary**

| key | MVS | API | meaning |
|:---|---:|---:|:---|
| `needs_offset` | 59 of 381 | 74 of 416 | the residue number in the request (a UniProt position, or a mature-protein number) is not the residue's author number in the structure, so the right answer applies a numbering offset |
| `author_label_numbers_differ` | 84 of 381 | 136 of 416 | the target residue's author number differs from its label (mmCIF) number |
| `chain_mismatch` | 67 of 381 | 88 of 416 | the target's author chain id differs from its label chain id |
| `needs_ligand_identity` | 60 of 381 | 29 of 416 | the request names a compound in words and the answer needs its component id |
| `needs_uniprot_mapping` | 82 of 381 | 97 of 416 | the answer needs a UniProt-to-structure residue mapping |
| `needs_structure_lookup` | 53 of 215 | 53 of 125 | the atoms asked for are not named in the request and must be found in the entry |
| `needs_entry_lookup` | 39 of 39 | – | the request names a protein, not an entry: the answer needs a PDB id |
| `insertion_code` | 3 of 297 | 3 of 207 | a target residue has an insertion code |
| `needs_referent_from_context` | 13 of 58 | 9 of 44 | a follow-up request names its object only through the start state ("it", "the red chain") |
| `hide_toggle` | – | 15 of 125 | an API twin that reaches the MVS scene only by switching off something the viewer draws by default, which the request does not state |
| `number_in_name_as_author_number_is_right` | 34 of 82 | 34 of 82 | clinical tier: using the number in the variant name directly as the author residue number gives the right residue (no mapping needed to be right) |
| `name_in_mature_numbering` | 13 of 82 | 13 of 82 | clinical tier: the variant name counts from the first residue of the mature protein, and the request says so |
| `alphafold_model` | 10 of 82 | 10 of 82 | clinical tier: the structure is an AlphaFold DB model (numbered as UniProt) |

"k of n": the fact holds in k of the n original tasks whose generator records it (`molbench/difficulty.py` maps each generator's own key names). *Not a run result: counted from the task files, so these numbers are real whatever answered the run.*
