> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Task success by difficulty fact (panel mean, all tiers)**

| key | MVS: tasks, yes | MVS: success, yes | MVS: tasks, no | MVS: success, no | API: tasks, yes | API: success, yes | API: tasks, no | API: success, no |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| `needs_offset` | 59 | 0.542 | 322 | 0.544 | 74 | 0.583 | 342 | 0.584 |
| `author_label_numbers_differ` | 84 | 0.538 | 297 | 0.545 | 136 | 0.584 | 280 | 0.584 |
| `chain_mismatch` | 67 | 0.545 | 314 | 0.543 | 88 | 0.582 | 328 | 0.584 |
| `needs_ligand_identity` | 60 | 0.545 | 321 | 0.543 | 29 | 0.600 | 387 | 0.582 |
| `needs_uniprot_mapping` | 82 | 0.535 | 299 | 0.546 | 97 | 0.583 | 319 | 0.584 |
| `needs_structure_lookup` | 53 | 0.535 | 162 | 0.552 | 53 | 0.582 | 72 | 0.582 |
| `needs_entry_lookup` | 39 | 0.551 | – | – | – | – | – | – |
| `insertion_code` | 3 | 0.519 | 294 | 0.544 | 3 | 0.593 | 204 | 0.582 |
| `needs_referent_from_context` | 13 | 0.548 | 45 | 0.539 | 9 | 0.557 | 35 | 0.572 |
| `hide_toggle` | – | – | – | – | 15 | 0.569 | 110 | 0.584 |
| `number_in_name_as_author_number_is_right` | 34 | 0.533 | 48 | 0.537 | 34 | 0.584 | 48 | 0.584 |
| `name_in_mature_numbering` | 13 | 0.568 | 69 | 0.529 | 13 | 0.595 | 69 | 0.582 |
| `alphafold_model` | 10 | 0.530 | 72 | 0.536 | 10 | 0.592 | 72 | 0.583 |

Original tasks whose generator records the fact. The two groups differ in tier mix as well, so read a row as a description, not as the effect of the fact; the clinical table holds the tier fixed.
