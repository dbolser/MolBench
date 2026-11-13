# Generated API-track tasks

Written by `scripts/generate_api_tasks.py` (seed 20261113); do not edit by hand. Re-running the script reproduces every file byte for byte (`--check`). The 20 curated tasks are in `tasks/api_calling/`.

116 tasks on 68 structures; 28 held back.

| tier | template (family) | tasks | share of the tier (both directories) | how the reference is derived |
|---|---|---:|---:|---|
| tool_only | `api-alphafold` | 2 | 3 of 33 (9%) | The panel's AlphaFold DB models, loaded with custom_data from the documented URL pattern, pLDDT colouring switched on, and a tooltip on a seeded range. |
| tool_only | `api-canvas` | 2 | 4 of 33 (12%) | Background, lighting and spin. |
| tool_only | `api-domain-overlay` | 2 | 3 of 33 (9%) | Entries with a UniProt mapping: domain annotation and sequence panel on (declared settings). |
| tool_only | `api-highlight` | 2 | 3 of 33 (9%) | The viewer's highlight on seeded author-numbered residues, with a highlight colour and focus. |
| tool_only | `api-ligand-view` | 3 | 3 of 33 (9%) | The PDBe ligand view of a single-copy ligand named by code, with a background colour. Compared by the ligand it names. |
| tool_only | `api-maps` | 2 | 2 of 33 (6%) | X-ray entries: electron-density maps on, one map styled (declared settings). |
| tool_only | `api-preset` | 2 | 2 of 33 (6%) | A load preset (unit cell or supercell for an X-ray entry, all models for an NMR ensemble) and a background colour. |
| tool_only | `api-superposition` | 2 | 3 of 33 (9%) | The PDBe-KB superposition view of a panel disease protein by UniProt accession. No structure entry; compared by settings. |
| tool_only | `api-symmetry-overlay` | 1 | 1 of 33 (3%) | An entry whose assembly 1 is built by symmetry: that assembly with the symmetry annotation on. |
| tool_only | `api-tooltips` | 3 | 3 of 33 (9%) | Tooltips on seeded author-numbered residues (the text is the residue's own name and number), waters hidden. |
| tool_only | `api-undo` | 3 | 3 of 33 (9%) | A request with a step that is undone again (reset camera, clear selection, clear highlight, reset selection colour). Only the final state is graded. |
| tool_only | `api-validation-overlay` | 2 | 3 of 33 (9%) | X-ray entries with waters: waters hidden, validation annotation on (a declared setting). |
| translation | `api-assembly` | 5 | 6 of 103 (6%) | Assembly 1 where the facts say it is built by symmetry from every deposited chain, plus a ligand or range colouring. The assembly is a fact of the state; atoms are compared on the deposited unit. |
| translation | `api-atoms` | 5 | 5 of 103 (5%) | Named atoms of a single-copy ligand (its metal, when it has one), or two side-chain atoms of a seeded residue under the ball-and-stick style. |
| translation | `api-chain-colour` | 8 | 10 of 103 (10%) | One or two chains of an entry whose author chain ids differ from the label chain ids, named by author id. The cartoon style is asked for unless the author chain is exactly the polymer chain, so every reading of 'chain X' gives the same picture. |
| translation | `api-entity` | 5 | 5 of 103 (5%) | Two polymer entities by entity id; intended atoms are the entity's label chains from the facts. Entity ids as numbers fail (the viewer compares with ===). |
| translation | `api-hide` | 8 | 11 of 103 (11%) | Hide toggles for components the entry has (waters, heteroatoms, carbohydrates on entries whose sugars are all branched, non-standard residues, polymer), with a colouring or a second toggle. |
| translation | `api-layered-colour` | 7 | 7 of 103 (7%) | A seeded author range and one residue inside it in another colour: one call in order, or two calls with keep_colors. The reverse order and two calls without keep_colors fail. |
| translation | `api-ligand` | 7 | 8 of 103 (8%) | A ligand from the frozen facts (more than five heavy atoms, not a crystallisation additive), named with its component code; coloured and focused. One copy by chain when each chain has one. |
| translation | `api-range-colour` | 8 | 9 of 103 (9%) | A seeded author-numbered range inside one run of a chain with a numbering offset; kept only if it selects exactly the polymer residues of the matching label range. A third of the tasks also colour everything else. |
| translation | `api-residue-colour` | 9 | 9 of 103 (9%) | 1-3 seeded residues of a protein chain whose author numbers differ from the label numbers; named as papers do (His57). Checked: author keys select exactly the residue of that name; the label form succeeds; the author number in `residue_number` fails. |
| translation | `api-residue-sticks` | 5 | 7 of 103 (7%) | The same, plus an added representation in the same colour (`representationColor`). Hinges on the viewer rule that `color` does not colour an added representation. |
| translation | `api-sticks-plain` | 3 | 3 of 103 (3%) | The same, with an added ball-and-stick and no recolouring (`color: null`; without the key the viewer paints its default orange). |
| translation | `api-style-colour` | 5 | 5 of 103 (5%) | A global style and a seeded author range colouring. The style has to be set first (setting it reloads and wipes colouring); the reverse order fails. |
| translation | `api-uniprot-range` | 6 | 6 of 103 (6%) | A seeded run of consecutive UniProt positions, selected with the viewer's UniProt range keys; same checks. |
| translation | `api-uniprot-residue` | 9 | 9 of 103 (9%) | 1-2 seeded UniProt positions from the frozen SIFTS table (observed, same residue as UniProt, author number != UniProt number), selected with the viewer's UniProt keys. Checked: the SIFTS rows in author numbering give the same atoms; the UniProt number as an author number fails. |

## Rules every task obeys

- The request names every structure by id, every residue by name and author number, every ligand by component code and every UniProt position with its accession, so the reference is determined by the request. No task uses 1HSG (the API prompt's worked example).
- The reference holds only what the request states (a bare load already draws the structure).
- Each selection is checked against a second statement of its atoms (`provenance.targets`), the reference grades itself as exactly right, a bare load scores 0, and the equivalent and wrong answers listed in `provenance.checks` succeed and fail as they should.
- `provenance.difficulty` records what makes the task hard: `numbering_offset` (author number differs from label number), `auth_label_chain`, `uniprot_mapping`, `ligand_identity_needed` (always false: codes are in the request), `hinges_on` (a viewer rule the task turns on), `order_matters`, `setting_only` (options compared as declared settings).
- Colours are from `molbench.drawn.TASK_PALETTE`.

## Held-back split

Held-back structures (15): 1hrc 1iep 1plc 1rx2 2c9v 3ert 3k34 3kcg 5edm 7a4m 8c86 8ce0 9fb2 9gio af-p68871-f1-model_v6. Rule: of the panel entries that no task used before this corpus, ranked by SHA-256 of `molbench-heldback-v1|<id>`, the first fifth of the panel, 8CE0 (held back by the fixture tasks) always among them; `data/panel/heldback.json` overrides it. No public task of this script uses one of them.

| tier | structures | held-back structures | tasks | held-back tasks |
|---|---:|---:|---:|---:|
| tool_only | 29 | 7 (24%) | 33 | 7 |
| translation | 73 | 14 (19%) | 103 | 21 |

## Viewer rules that tasks turn on

Of the 136 API tasks in both directories: `added_representation_colour` 10 (7%); `default_select_colour` 3 (2%).

## Viewer surface exercised (references of both directories)

| surface | name | tasks |
|---|---|---:|
| action | `load` | 136 |
| action | `set_visual_style` | 25 |
| action | `set_property` | 42 |
| action | `color` | 96 |
| action | `focus` | 9 |
| action | `highlight` | 4 |
| action | `tooltips` | 6 |
| action | `set_color` | 2 |
| action | `reset` | 1 |
| action | `clear_highlight` | 1 |
| action | `clear_selection` | 1 |
| action | `clear_tooltips` | 0 |
| property | `hide_polymer` | 3 |
| property | `hide_water` | 21 |
| property | `hide_heteroatoms` | 2 |
| property | `hide_carbs` | 3 |
| property | `hide_non_standard` | 2 |
| property | `hide_coarse` | 0 |
| property | `spin` | 4 |
| property | `superposition` | 3 |
| property | `superposition_params` | 0 |
| property | `load_maps` | 2 |
| property | `map_settings` | 2 |
| property | `validation_annotation` | 3 |
| property | `domain_annotation` | 3 |
| property | `symmetry_annotation` | 1 |
| property | `alphafold_view` | 3 |
| property | `sequence_panel` | 2 |
| property | `bg_color` | 11 |
| property | `highlight_color` | 0 |
| property | `select_color` | 0 |
| property | `lighting` | 4 |
| selector key | `entity_id` | 5 |
| selector key | `struct_asym_id` | 0 |
| selector key | `auth_asym_id` | 67 |
| selector key | `label_comp_id` | 22 |
| selector key | `residue_number` | 0 |
| selector key | `start_residue_number` | 1 |
| selector key | `end_residue_number` | 1 |
| selector key | `auth_seq_id` | 35 |
| selector key | `auth_residue_number` | 0 |
| selector key | `auth_ins_code_id` | 0 |
| selector key | `start_auth_residue_number` | 28 |
| selector key | `end_auth_residue_number` | 28 |
| selector key | `start_auth_ins_code_id` | 0 |
| selector key | `end_auth_ins_code_id` | 0 |
| selector key | `uniprot_accession` | 15 |
| selector key | `uniprot_residue_number` | 9 |
| selector key | `start_uniprot_residue_number` | 6 |
| selector key | `end_uniprot_residue_number` | 6 |
| selector key | `atoms` | 5 |
| selector key | `atom_id` | 0 |
| visual style | `cartoon` | 17 |
| visual style | `ball-and-stick` | 4 |
| visual style | `carbohydrate` | 0 |
| visual style | `ellipsoid` | 0 |
| visual style | `gaussian-surface` | 0 |
| visual style | `molecular-surface` | 4 |
| visual style | `point` | 0 |
| visual style | `putty` | 0 |
| visual style | `spacefill` | 0 |
| selection attribute | `color` | 95 |
| selection attribute | `representation` | 14 |
| selection attribute | `representationColor` | 11 |
| selection attribute | `sideChain` | 0 |
| selection attribute | `focus` | 0 |
| selection attribute | `tooltip` | 6 |
| selection attribute | `representation=cartoon` | 0 |
| selection attribute | `representation=ball-and-stick` | 11 |
| selection attribute | `representation=carbohydrate` | 0 |
| selection attribute | `representation=ellipsoid` | 0 |
| selection attribute | `representation=gaussian-surface` | 0 |
| selection attribute | `representation=molecular-surface` | 1 |
| selection attribute | `representation=point` | 0 |
| selection attribute | `representation=putty` | 0 |
| selection attribute | `representation=spacefill` | 2 |
| load option | `molecule_id` | 133 |
| load option | `custom_data` | 3 |
| load option | `assembly_id` | 7 |
| load option | `preset` | 2 |
| load option | `ligand_view` | 3 |
| load option | `alphafold` | 0 |
| call option | `color.non_selected_color` | 7 |
| call option | `color.keep_colors` | 5 |
| call option | `color.keep_representations` | 0 |
| call option | `highlight.color` | 2 |
| call option | `highlight.focus` | 2 |
| call option | `set_color.highlight` | 2 |
| call option | `set_color.select` | 2 |
| call option | `reset.camera` | 0 |
| call option | `reset.theme` | 0 |
| call option | `reset.highlightColor` | 0 |
| call option | `reset.selectColor` | 1 |

## Structures a template skipped

- `api-undo`: 32 skipped (a check failed, e.g. a water shares the author numbers of the range)
