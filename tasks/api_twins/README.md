# API twins of MVS tasks

Written by `scripts/translate_mvs_to_api.py --all`; do not edit by hand. A twin has the prompt, structures, split, style, tier, family and target atoms of its MVS task, and a call list whose replayed final state is the MVS reference's drawn state (same atoms, representations and colours; nothing else drawn). `twin_of` links the two both ways.

Run this script last, after every MVS generator: it writes `twin_of` into the MVS task files, so re-running an MVS generator afterwards removes those links (run this script again), and an MVS generator's own byte-for-byte rebuild check has to leave `twin_of` out of its comparison.

- MVS tasks read: 378
- already paired by their own generator (clinical, follow-up, accept-set, paraphrases): 130
- left without an API counterpart by a generator that writes both tracks: 33
- in the old task format (no `twin_of` field, so no twin is written): 0, of which the API could express 0
- left for this script: 215; **twins written: 125 (58%)**
- MVS tasks with an API twin, all generators together: 255 of 378 (67%)

## Twins by template

| tier | family | MVS tasks | twins |
|---|---|---:|---:|
| grounded | `gr-all-but-chain` | 3 | 3 |
| grounded | `gr-attachment` | 4 | 4 |
| grounded | `gr-catalytic` | 6 | 6 |
| grounded | `gr-disulfides` | 6 | 6 |
| grounded | `gr-entity` | 6 | 6 |
| grounded | `gr-glyco-sites` | 5 | 5 |
| grounded | `gr-heme` | 4 | 4 |
| grounded | `gr-heme-axial` | 4 | 4 |
| grounded | `gr-ligand` | 6 | 6 |
| grounded | `gr-longest-helix` | 4 | 4 |
| grounded | `gr-metal-site` | 6 | 6 |
| grounded | `gr-modres` | 5 | 5 |
| grounded | `gr-nucleic` | 5 | 5 |
| grounded | `gr-secstruct` | 4 | 4 |
| interactions | `in-ca-distance` | 5 | 0 |
| interactions | `in-computed` | 5 | 0 |
| interactions | `in-disulfide` | 5 | 0 |
| interactions | `in-hbond` | 5 | 0 |
| interactions | `in-ligand-contact` | 5 | 0 |
| interactions | `in-metal-contact` | 5 | 0 |
| interactions | `in-salt-bridge` | 5 | 0 |
| interactions | `in-transparent` | 5 | 0 |
| resolve | `res-complex` | 3 | 0 |
| resolve | `res-dna` | 3 | 0 |
| resolve | `res-gene` | 11 | 0 |
| resolve | `res-ligand` | 10 | 0 |
| resolve | `res-name` | 12 | 0 |
| translation | `tr-cartoon` | 4 | 4 |
| translation | `tr-chain-colour` | 4 | 4 |
| translation | `tr-chain-only` | 4 | 4 |
| translation | `tr-chains-named` | 4 | 4 |
| translation | `tr-colour-by-chain` | 5 | 0 |
| translation | `tr-glycans` | 4 | 4 |
| translation | `tr-het-code` | 4 | 4 |
| translation | `tr-ions` | 4 | 4 |
| translation | `tr-ligands` | 4 | 4 |
| translation | `tr-range-labels` | 4 | 0 |
| translation | `tr-range-rows` | 4 | 4 |
| translation | `tr-range-sticks` | 5 | 5 |
| translation | `tr-rep-word` | 4 | 2 |
| translation | `tr-residue-focus` | 4 | 4 |
| translation | `tr-strands` | 3 | 3 |
| translation | `tr-surface` | 4 | 4 |
| translation | `tr-water` | 3 | 3 |

## How the twins reach the picture

An MVS scene draws only what it lists; a `load` draws the whole entry. So a twin has to take away what the scene does not draw: with hide toggles (`provenance.twin.switched_off`) or with a global style that draws polymer only (`provenance.twin.base`). The request says what to show, not what to remove, so task success on a twin also asks the model to know what a load draws by default. The paired analysis should report twins with and without such steps separately (`provenance.difficulty.context_switched_off`, `order_matters`); the target score does not depend on them.

- base: the cartoon style 115; the default view 4; the molecular-surface style 4; the spacefill style 2
- hide toggles: `hide_carbs` 2; `hide_heteroatoms` 6; `hide_polymer` 12; `hide_water` 5
- twins on the default view with nothing switched off: 3
- twins with an added, coloured representation (`representationColor`): 84

| surface | name | twins |
|---|---|---:|
| action | `color` | 125 |
| action | `focus` | 4 |
| action | `load` | 125 |
| action | `set_property` | 18 |
| action | `set_visual_style` | 121 |
| call option | `color.non_selected_color` | 89 |
| property | `hide_carbs` | 2 |
| property | `hide_heteroatoms` | 6 |
| property | `hide_polymer` | 12 |
| property | `hide_water` | 5 |
| selection attribute | `color` | 86 |
| selection attribute | `representation` | 84 |
| selection attribute | `representationColor` | 84 |
| selector key | `auth_asym_id` | 60 |
| selector key | `auth_seq_id` | 42 |
| selector key | `end_auth_residue_number` | 11 |
| selector key | `end_residue_number` | 8 |
| selector key | `entity_id` | 17 |
| selector key | `label_comp_id` | 28 |
| selector key | `start_auth_residue_number` | 11 |
| selector key | `start_residue_number` | 8 |
| selector key | `struct_asym_id` | 24 |
| visual style | `cartoon` | 115 |
| visual style | `molecular-surface` | 4 |
| visual style | `spacefill` | 2 |

## MVS tasks without a twin from this script

| reason | tasks |
|---|---:|
| already has a twin from its own generator | 130 |
| the structure is named by protein and entries outside the panel are accepted | 39 |
| left without an API counterpart by its own two-track generator | 33 |
| a distance line or another drawn primitive | 30 |
| a colour theme (colour by chain) | 5 |
| the computed non-covalent interactions request | 5 |
| transparency (the API has no opacity) | 5 |
| a 3D text label | 4 |
| a representation with no API counterpart | 2 |

| MVS task | tier | reason | detail |
|---|---|---|---|
| `acc-metal-copy-1tup-mvs` | accept_set | left without an API counterpart by its own two-track generator | scripts/generate_accept_set_tasks.py |
| `acc-metal-copy-8eph-mvs` | accept_set | left without an API counterpart by its own two-track generator | scripts/generate_accept_set_tasks.py |
| `acc-metal-copy-9fb2-mvs` | accept_set | left without an API counterpart by its own two-track generator | scripts/generate_accept_set_tasks.py |
| `acc-metal-which-1udt-mvs` | accept_set | left without an API counterpart by its own two-track generator | scripts/generate_accept_set_tasks.py |
| `acc-metal-which-7a4m-mvs` | accept_set | left without an API counterpart by its own two-track generator | scripts/generate_accept_set_tasks.py |
| `acc-representation-open-1hrc-mvs` | accept_set | left without an API counterpart by its own two-track generator | scripts/generate_accept_set_tasks.py |
| `acc-representation-open-1mbn-mvs` | accept_set | left without an API counterpart by its own two-track generator | scripts/generate_accept_set_tasks.py |
| `acc-representation-open-3f9m-mvs` | accept_set | left without an API counterpart by its own two-track generator | scripts/generate_accept_set_tasks.py |
| `acc-residue-copy-1trn-mvs` | accept_set | left without an API counterpart by its own two-track generator | scripts/generate_accept_set_tasks.py |
| `acc-residue-copy-2hhb-mvs` | accept_set | left without an API counterpart by its own two-track generator | scripts/generate_accept_set_tasks.py |
| `acc-residue-copy-5ni1-mvs` | accept_set | left without an API counterpart by its own two-track generator | scripts/generate_accept_set_tasks.py |
| `fu-add-chain-1lmb-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-add-chain-3ave-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-add-label-1stp-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-add-label-3ptb-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-add-ligand-5cj6-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-add-ligand-5ni1-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-it-colour-1hrc-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-it-colour-3ptb-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-it-surface-9f69-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-noop-spin-1c3w-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-noop-spin-8k7f-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-only-chain-1aoi-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-only-chain-5uak-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-opacity-1a6m-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-opacity-1iep-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-remove-label-3f9m-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-remove-ligand-1k4c-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-remove-ligand-3eml-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-rep-ligand-1hvr-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-rep-ligand-1k4c-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-rep-polymer-6tha-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `fu-rep-polymer-8c86-mvs` | followup | left without an API counterpart by its own two-track generator | scripts/generate_followup_tasks.py |
| `in-ca-distance-1ake` | interactions | a distance line or another drawn primitive |  |
| `in-ca-distance-1hho` | interactions | a distance line or another drawn primitive |  |
| `in-ca-distance-8c86` | interactions | a distance line or another drawn primitive |  |
| `in-ca-distance-8k7f` | interactions | a distance line or another drawn primitive |  |
| `in-ca-distance-9fb2` | interactions | a distance line or another drawn primitive |  |
| `in-computed-1a6m-hem` | interactions | the computed non-covalent interactions request |  |
| `in-computed-1c3w-ret` | interactions | the computed non-covalent interactions request |  |
| `in-computed-1rx2-nap` | interactions | the computed non-covalent interactions request |  |
| `in-computed-3ptb-ben` | interactions | the computed non-covalent interactions request |  |
| `in-computed-9f69-dxx` | interactions | the computed non-covalent interactions request |  |
| `in-disulfide-1f88` | interactions | a distance line or another drawn primitive |  |
| `in-disulfide-1trn` | interactions | a distance line or another drawn primitive |  |
| `in-disulfide-2nwd` | interactions | a distance line or another drawn primitive |  |
| `in-disulfide-2ptc` | interactions | a distance line or another drawn primitive |  |
| `in-disulfide-6vxx` | interactions | a distance line or another drawn primitive |  |
| `in-hbond-1a3k` | interactions | a distance line or another drawn primitive |  |
| `in-hbond-1iep` | interactions | a distance line or another drawn primitive |  |
| `in-hbond-1lmb` | interactions | a distance line or another drawn primitive |  |
| `in-hbond-3ave` | interactions | a distance line or another drawn primitive |  |
| `in-hbond-4ins` | interactions | a distance line or another drawn primitive |  |
| `in-ligand-contact-1atp-atp` | interactions | a distance line or another drawn primitive |  |
| `in-ligand-contact-1cbs-rea` | interactions | a distance line or another drawn primitive |  |
| `in-ligand-contact-1rx2-nap` | interactions | a distance line or another drawn primitive |  |
| `in-ligand-contact-1stp-btn` | interactions | a distance line or another drawn primitive |  |
| `in-ligand-contact-2cpp-cam` | interactions | a distance line or another drawn primitive |  |
| `in-metal-contact-1hrc-hec` | interactions | a distance line or another drawn primitive |  |
| `in-metal-contact-1mbn-hem` | interactions | a distance line or another drawn primitive |  |
| `in-metal-contact-1plc-cu` | interactions | a distance line or another drawn primitive |  |
| `in-metal-contact-1udt-mg` | interactions | a distance line or another drawn primitive |  |
| `in-metal-contact-3kcg-ca` | interactions | a distance line or another drawn primitive |  |
| `in-salt-bridge-1ema` | interactions | a distance line or another drawn primitive |  |
| `in-salt-bridge-1igt` | interactions | a distance line or another drawn primitive |  |
| `in-salt-bridge-1k4c` | interactions | a distance line or another drawn primitive |  |
| `in-salt-bridge-2p4e` | interactions | a distance line or another drawn primitive |  |
| `in-salt-bridge-5uak` | interactions | a distance line or another drawn primitive |  |
| `in-transparent-1ctq-gnp` | interactions | transparency (the API has no opacity) |  |
| `in-transparent-1rx2-nap` | interactions | transparency (the API has no opacity) |  |
| `in-transparent-3eml-zma` | interactions | transparency (the API has no opacity) |  |
| `in-transparent-3ert-oht` | interactions | transparency (the API has no opacity) |  |
| `in-transparent-3f9m-glc` | interactions | transparency (the API has no opacity) |  |
| `res-complex-p00760-p00974` | resolve | the structure is named by protein and entries outside the panel are accepted | 30 of 30 other accepted entries have no atom table |
| `res-complex-p40337-q15369-q15370` | resolve | the structure is named by protein and entries outside the panel are accepted | 139 of 139 other accepted entries have no atom table |
| `res-complex-p69905-p68871` | resolve | the structure is named by protein and entries outside the panel are accepted | 341 of 343 other accepted entries have no atom table |
| `res-dna-p03034` | resolve | the structure is named by protein and entries outside the panel are accepted | 5 of 5 other accepted entries have no atom table |
| `res-dna-p04637` | resolve | the structure is named by protein and entries outside the panel are accepted | 46 of 46 other accepted entries have no atom table |
| `res-dna-p08046` | resolve | the structure is named by protein and entries outside the panel are accepted | 19 of 19 other accepted entries have no atom table |
| `res-gene-p00441` | resolve | the structure is named by protein and entries outside the panel are accepted | 146 of 146 other accepted entries have no atom table |
| `res-gene-p01009` | resolve | the structure is named by protein and entries outside the panel are accepted | 46 of 46 other accepted entries have no atom table |
| `res-gene-p01112` | resolve | the structure is named by protein and entries outside the panel are accepted | 254 of 254 other accepted entries have no atom table |
| `res-gene-p04062` | resolve | the structure is named by protein and entries outside the panel are accepted | 57 of 57 other accepted entries have no atom table |
| `res-gene-p07320` | resolve | the structure is named by protein and entries outside the panel are accepted | 15 of 15 other accepted entries have no atom table |
| `res-gene-p07477` | resolve | the structure is named by protein and entries outside the panel are accepted | 10 of 10 other accepted entries have no atom table |
| `res-gene-p11166` | resolve | the structure is named by protein and entries outside the panel are accepted | 4 of 4 other accepted entries have no atom table |
| `res-gene-p17931` | resolve | the structure is named by protein and entries outside the panel are accepted | 182 of 182 other accepted entries have no atom table |
| `res-gene-p29274` | resolve | the structure is named by protein and entries outside the panel are accepted | 191 of 191 other accepted entries have no atom table |
| `res-gene-p60174` | resolve | the structure is named by protein and entries outside the panel are accepted | 23 of 23 other accepted entries have no atom table |
| `res-gene-q8nbp7` | resolve | the structure is named by protein and entries outside the panel are accepted | 59 of 59 other accepted entries have no atom table |
| `res-ligand-o76074-via` | resolve | the structure is named by protein and entries outside the panel are accepted | 3 of 3 other accepted entries have no atom table |
| `res-ligand-p00520-sti` | resolve | the structure is named by protein and entries outside the panel are accepted | 6 of 6 other accepted entries have no atom table |
| `res-ligand-p02699-ret` | resolve | the structure is named by protein and entries outside the panel are accepted | 35 of 35 other accepted entries have no atom table |
| `res-ligand-p02945-ret` | resolve | the structure is named by protein and entries outside the panel are accepted | 169 of 169 other accepted entries have no atom table |
| `res-ligand-p03372-oht` | resolve | the structure is named by protein and entries outside the panel are accepted | 6 of 6 other accepted entries have no atom table |
| `res-ligand-p05132-atp` | resolve | the structure is named by protein and entries outside the panel are accepted | 12 of 12 other accepted entries have no atom table |
| `res-ligand-p0abq4-fol` | resolve | the structure is named by protein and entries outside the panel are accepted | 85 of 85 other accepted entries have no atom table |
| `res-ligand-p22629-btn` | resolve | the structure is named by protein and entries outside the panel are accepted | 51 of 51 other accepted entries have no atom table |
| `res-ligand-p29373-rea` | resolve | the structure is named by protein and entries outside the panel are accepted | 3 of 3 other accepted entries have no atom table |
| `res-ligand-p69441-ap5` | resolve | the structure is named by protein and entries outside the panel are accepted | 15 of 15 other accepted entries have no atom table |
| `res-name-p00004` | resolve | the structure is named by protein and entries outside the panel are accepted | 31 of 31 other accepted entries have no atom table |
| `res-name-p00183` | resolve | the structure is named by protein and entries outside the panel are accepted | 128 of 128 other accepted entries have no atom table |
| `res-name-p00299` | resolve | the structure is named by protein and entries outside the panel are accepted | 15 of 15 other accepted entries have no atom table |
| `res-name-p02185` | resolve | the structure is named by protein and entries outside the panel are accepted | 356 of 357 other accepted entries have no atom table |
| `res-name-p02649` | resolve | the structure is named by protein and entries outside the panel are accepted | 27 of 27 other accepted entries have no atom table |
| `res-name-p02931` | resolve | the structure is named by protein and entries outside the panel are accepted | 47 of 47 other accepted entries have no atom table |
| `res-name-p09528` | resolve | the structure is named by protein and entries outside the panel are accepted | 26 of 26 other accepted entries have no atom table |
| `res-name-p0dtc2` | resolve | the structure is named by protein and entries outside the panel are accepted | 2171 of 2171 other accepted entries have no atom table |
| `res-name-p10275` | resolve | the structure is named by protein and entries outside the panel are accepted | 93 of 93 other accepted entries have no atom table |
| `res-name-p35557` | resolve | the structure is named by protein and entries outside the panel are accepted | 34 of 34 other accepted entries have no atom table |
| `res-name-p42212` | resolve | the structure is named by protein and entries outside the panel are accepted | 643 of 643 other accepted entries have no atom table |
| `res-name-p61626` | resolve | the structure is named by protein and entries outside the panel are accepted | 213 of 213 other accepted entries have no atom table |
| `tr-colour-by-chain-1aoi` | translation | a colour theme (colour by chain) | chain-id |
| `tr-colour-by-chain-1tup` | translation | a colour theme (colour by chain) | chain-id |
| `tr-colour-by-chain-2hhb` | translation | a colour theme (colour by chain) | chain-id |
| `tr-colour-by-chain-3kcg` | translation | a colour theme (colour by chain) | chain-id |
| `tr-colour-by-chain-9gio` | translation | a colour theme (colour by chain) | chain-id |
| `tr-range-labels-1a6m` | translation | a 3D text label |  |
| `tr-range-labels-1hrc` | translation | a 3D text label |  |
| `tr-range-labels-2ptc` | translation | a 3D text label |  |
| `tr-range-labels-3ptb` | translation | a 3D text label |  |
| `tr-rep-word-1udt` | translation | a representation with no API counterpart | backbone |
| `tr-rep-word-2nwd` | translation | a representation with no API counterpart | line |
