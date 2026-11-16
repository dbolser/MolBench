**Corpus: difficulty facts under one vocabulary**

| key | MVS | API | meaning |
|:---|---:|---:|:---|
| `needs_offset` | 57 of 378 | 72 of 403 | the residue number in the request (a UniProt position, or a mature-protein number) is not the residue's author number in the structure, so the right answer applies a numbering offset |
| `author_label_numbers_differ` | 87 of 378 | 134 of 403 | the target residue's author number differs from its label (mmCIF) number |
| `chain_mismatch` | 65 of 378 | 78 of 403 | the target's author chain id differs from its label chain id |
| `needs_ligand_identity` | 61 of 378 | 29 of 403 | the request names a compound in words and the answer needs its component id |
| `needs_uniprot_mapping` | 79 of 378 | 94 of 403 | the answer needs a UniProt-to-structure residue mapping |
| `needs_structure_lookup` | 58 of 215 | 58 of 125 | the atoms asked for are not named in the request and must be found in the entry |
| `needs_entry_lookup` | 39 of 39 | – | the request names a protein, not an entry: the answer needs a PDB id |
| `insertion_code` | 4 of 294 | 4 of 204 | a target residue has an insertion code |
| `needs_referent_from_context` | 13 of 58 | 9 of 44 | a follow-up request names its object only through the start state ("it", "the red chain") |
| `hide_toggle` | – | 18 of 125 | an API twin that reaches the MVS scene only by switching off something the viewer draws by default, which the request does not state |
| `number_in_name_as_author_number_is_right` | 34 of 79 | 34 of 79 | clinical tier: using the number in the variant name directly as the author residue number gives the right residue (no mapping needed to be right) |
| `name_in_mature_numbering` | 14 of 79 | 14 of 79 | clinical tier: the variant name counts from the first residue of the mature protein, and the request says so |
| `alphafold_model` | 7 of 79 | 7 of 79 | clinical tier: the structure is an AlphaFold DB model (numbered as UniProt) |

"k of n": the fact holds in k of the n original tasks whose generator records it (`molbench/difficulty.py` maps each generator's own key names). *Not a run result: counted from the task files, so these numbers are real whatever answered the run.*
