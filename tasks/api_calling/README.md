# Curated API-track tasks

The 20 tasks of July 2026 as repaired in phase A, rebuilt in the task format by `scripts/generate_api_tasks.py` (function `curated`); do not edit by hand. Ids, file names and references are unchanged. Where a ligand was named in words only, its component code was added to the request (`provenance.prompt_change`). The generated tasks are in `tasks/api_generated/`.

20 tasks on 14 structures; 0 held back.

| tier | template (family) | tasks | share of the tier (both directories) | how the reference is derived |
|---|---|---:|---:|---|
| tool_only | `api-alphafold` | 1 | 3 of 34 (9%) | The panel's AlphaFold DB models, loaded with custom_data from the documented URL pattern, pLDDT colouring switched on, and a tooltip on a seeded range. |
| tool_only | `api-canvas` | 2 | 4 of 34 (12%) | Background, lighting and spin. |
| tool_only | `api-domain-overlay` | 1 | 3 of 34 (9%) | Entries with a UniProt mapping: domain annotation and sequence panel on (declared settings). |
| tool_only | `api-highlight` | 1 | 3 of 34 (9%) | The viewer's highlight on seeded author-numbered residues, with a highlight colour and focus. |
| tool_only | `api-superposition` | 1 | 3 of 34 (9%) | The PDBe-KB superposition view of a panel disease protein by UniProt accession. No structure entry; compared by settings. |
| tool_only | `api-validation-overlay` | 1 | 3 of 34 (9%) | X-ray entries with waters: waters hidden, validation annotation on (a declared setting). |
| translation | `api-assembly` | 1 | 6 of 116 (5%) | Assembly 1 where the facts say it is built by symmetry from every deposited chain, plus a ligand or range colouring. The assembly is a fact of the state; atoms are compared on the deposited unit. |
| translation | `api-chain-colour` | 2 | 10 of 116 (9%) | One or two chains of an entry whose author chain ids differ from the label chain ids, named by author id. The cartoon style is asked for unless the author chain is exactly the polymer chain, so every reading of 'chain X' gives the same picture. |
| translation | `api-hide` | 3 | 11 of 116 (9%) | Hide toggles for components the entry has (waters, heteroatoms, carbohydrates on entries whose sugars are all branched, non-standard residues, polymer), with a colouring or a second toggle. |
| translation | `api-ligand` | 1 | 8 of 116 (7%) | A ligand from the frozen facts (more than five heavy atoms, not a crystallisation additive), named with its component code; coloured and focused. One copy by chain when each chain has one. |
| translation | `api-ligand-sticks` | 3 | 3 of 116 (3%) | (curated only) A ligand or modified residue as an added, coloured representation under the cartoon style. |
| translation | `api-range-colour` | 1 | 9 of 116 (8%) | A seeded author-numbered range inside one run of a chain with a numbering offset; kept only if it selects exactly the polymer residues of the matching label range. A third of the tasks also colour everything else. |
| translation | `api-residue-sticks` | 2 | 7 of 116 (6%) | The same, plus an added representation in the same colour (`representationColor`). Hinges on the viewer rule that `color` does not colour an added representation. |

## Rules every task obeys

- The request names every structure by id, every residue by name and author number, every ligand by component code and every UniProt position with its accession, so the reference is determined by the request. No task uses 1HSG (the API prompt's worked example).
- The reference holds only what the request states (a bare load already draws the structure).
- Each selection is checked against a second statement of its atoms (`provenance.targets`), the reference grades itself as exactly right, a bare load scores 0, and the equivalent and wrong answers listed in `provenance.checks` succeed and fail as they should.
- `provenance.difficulty` records what makes the task hard: `numbering_offset` (author number differs from label number), `auth_label_chain`, `uniprot_mapping`, `ligand_identity_needed` (always false: codes are in the request), `hinges_on` (a viewer rule the task turns on), `order_matters`, `setting_only` (options compared as declared settings).
- Colours are from `molbench.drawn.TASK_PALETTE`.
