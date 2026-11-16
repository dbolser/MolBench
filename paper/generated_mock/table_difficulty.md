> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Task success by difficulty fact (panel mean, all tiers)**

| key | MVS: tasks, yes | MVS: success, yes | MVS: tasks, no | MVS: success, no | API: tasks, yes | API: success, yes | API: tasks, no | API: success, no |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| `needs_offset` | 57 | 0.536 | 321 | 0.542 | 72 | 0.574 | 331 | 0.581 |
| `author_label_numbers_differ` | 87 | 0.536 | 291 | 0.543 | 134 | 0.579 | 269 | 0.580 |
| `chain_mismatch` | 65 | 0.544 | 313 | 0.541 | 78 | 0.587 | 325 | 0.578 |
| `needs_ligand_identity` | 61 | 0.545 | 317 | 0.541 | 29 | 0.600 | 374 | 0.578 |
| `needs_uniprot_mapping` | 79 | 0.530 | 299 | 0.545 | 94 | 0.576 | 309 | 0.581 |
| `needs_structure_lookup` | 58 | 0.537 | 157 | 0.551 | 58 | 0.580 | 67 | 0.579 |
| `needs_entry_lookup` | 39 | 0.551 | – | – | – | – | – | – |
| `insertion_code` | 4 | 0.492 | 290 | 0.543 | 4 | 0.583 | 200 | 0.578 |
| `needs_referent_from_context` | 13 | 0.542 | 45 | 0.537 | 9 | 0.554 | 35 | 0.563 |
| `hide_toggle` | – | – | – | – | 18 | 0.562 | 107 | 0.582 |
| `number_in_name_as_author_number_is_right` | 34 | 0.527 | 45 | 0.533 | 34 | 0.577 | 45 | 0.575 |
| `name_in_mature_numbering` | 14 | 0.552 | 65 | 0.526 | 14 | 0.577 | 65 | 0.576 |
| `alphafold_model` | 7 | 0.526 | 72 | 0.531 | 7 | 0.596 | 72 | 0.574 |

Original tasks whose generator records the fact. The two groups differ in tier mix as well, so read a row as a description, not as the effect of the fact; the clinical table holds the tier fixed.
