# API twins of MVS tasks

Written by `scripts/translate_mvs_to_api.py --all`; do not edit by hand. A twin has the prompt, structures, split, style, tier, family and target atoms of its MVS task, and a call list whose replayed final state is the MVS reference's drawn state (same atoms, representations and colours; nothing else drawn). `twin_of` links the two both ways.

70 MVS tasks read (0 in the task format, 70 in the old format); 0 twins written. The API can express the reference of 58 of the 70 (83%).


## MVS tasks without a twin

| reason | tasks |
|---|---:|
| old task format (no twin_of field); a twin could be made | 58 |
| the structure is named by protein and entries outside the panel are accepted | 6 |
| a distance line or another drawn primitive | 3 |
| the computed non-covalent interactions request | 2 |
| transparency (the API has no opacity) | 1 |

| MVS task | tier | reason | detail |
|---|---|---|---|
| `clinvar-1tup-D281` | clinical | old task format (no twin_of field); a twin could be made |  |
| `clinvar-1tup-F109` | clinical | old task format (no twin_of field); a twin could be made |  |
| `clinvar-1tup-N239` | clinical | old task format (no twin_of field); a twin could be made |  |
| `clinvar-1tup-S215` | clinical | old task format (no twin_of field); a twin could be made |  |
| `clinvar-1tup-S241` | clinical | old task format (no twin_of field); a twin could be made |  |
| `gen-cartoon-1cbs` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-cartoon-1hho` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-cartoon-1lyz` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-cartoon-2hhb` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-cartoon-3ptb` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-cartoon-4ins` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-chain-1cbs` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-chain-1hho` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-chain-1lyz` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-chain-2hhb` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-chain-3ptb` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-chain-4ins` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-focus-1cbs` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-focus-1hho` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-focus-2hhb` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-focus-3ptb` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-ions-1hho` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-ions-2hhb` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-ions-3ptb` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-ions-4ins` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-ligands-1cbs` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-ligands-1hho` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-ligands-2hhb` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-ligands-3ptb` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-range-1cbs` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-range-1hho` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-range-1lyz` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-range-2hhb` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-range-3ptb` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-range-4ins` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-surface-1cbs` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-surface-1hho` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-surface-1lyz` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-surface-2hhb` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-surface-3ptb` | translation | old task format (no twin_of field); a twin could be made |  |
| `gen-surface-4ins` | translation | old task format (no twin_of field); a twin could be made |  |
| `grd-disulfide-1lyz` | grounded | old task format (no twin_of field); a twin could be made |  |
| `grd-disulfide-3ptb` | grounded | old task format (no twin_of field); a twin could be made |  |
| `grd-disulfide-4ins` | grounded | old task format (no twin_of field); a twin could be made |  |
| `grd-ligand-1cbs-rea` | grounded | old task format (no twin_of field); a twin could be made |  |
| `grd-ligand-1hho-hem` | grounded | old task format (no twin_of field); a twin could be made |  |
| `grd-ligand-2hhb-hem` | grounded | old task format (no twin_of field); a twin could be made |  |
| `grd-ligand-3ptb-ca` | grounded | old task format (no twin_of field); a twin could be made |  |
| `grd-ligand-4ins-zn` | grounded | old task format (no twin_of field); a twin could be made |  |
| `hotspots-1tup` | clinical | old task format (no twin_of field); a twin could be made |  |
| `int-001` | interactions | a distance line or another drawn primitive |  |
| `int-002` | interactions | a distance line or another drawn primitive |  |
| `int-003` | interactions | a distance line or another drawn primitive |  |
| `int-004` | interactions | the computed non-covalent interactions request |  |
| `int-005` | interactions | the computed non-covalent interactions request |  |
| `int-006` | interactions | transparency (the API has no opacity) |  |
| `mvs-001` | translation | old task format (no twin_of field); a twin could be made |  |
| `mvs-002` | translation | old task format (no twin_of field); a twin could be made |  |
| `mvs-003` | translation | old task format (no twin_of field); a twin could be made |  |
| `mvs-004` | translation | old task format (no twin_of field); a twin could be made |  |
| `mvs-005` | translation | old task format (no twin_of field); a twin could be made |  |
| `named-1tup-143` | clinical | old task format (no twin_of field); a twin could be made |  |
| `named-1tup-175` | clinical | old task format (no twin_of field); a twin could be made |  |
| `named-1tup-248` | clinical | old task format (no twin_of field); a twin could be made |  |
| `res-cftr` | resolve | the structure is named by protein and entries outside the panel are accepted | 23 of 23 other accepted entries have no atom table |
| `res-gfp` | resolve | the structure is named by protein and entries outside the panel are accepted | 636 of 636 other accepted entries have no atom table |
| `res-lysozyme` | resolve | the structure is named by protein and entries outside the panel are accepted | 1396 of 1397 other accepted entries have no atom table |
| `res-myoglobin` | resolve | the structure is named by protein and entries outside the panel are accepted | 355 of 356 other accepted entries have no atom table |
| `res-pcsk9` | resolve | the structure is named by protein and entries outside the panel are accepted | 65 of 65 other accepted entries have no atom table |
| `res-pde5a` | resolve | the structure is named by protein and entries outside the panel are accepted | 49 of 49 other accepted entries have no atom table |
