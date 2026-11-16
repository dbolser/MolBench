# The MolBench corpus

Written by `scripts/corpus_report.py`; do not edit. Every number below is counted from the task files through `molbench.tasks.load_corpus()`; the sections after "Rulings applied" are `data/corpus/corpus_notes.md`, word for word. Format: `TASK_FORMAT.md`. Grading: `GRADING.md`. Each tier directory has its own generated `README.md` with templates and how each reference is derived.

**Not frozen yet.** The manifest names the corpus version and pins the hash at the freeze. Hash of `tasks/` on disk now: `ea9d32276bd33c66e3d892b3811e32dad40a71694d15c6834c69d3fb085ea7fa`.

## Size

885 task files: **803 original tasks** (384 MVS, 419 API) and **82 paraphrases** of 41 of them.

Original tasks by track, tier and split (public / held back):

| tier | MVS public | MVS held back | MVS total | API public | API held back | API total |
|---|---:|---:|---:|---:|---:|---:|
| translation | 55 | 18 | 73 | 138 | 40 | 178 |
| grounded | 52 | 11 | 63 | 52 | 11 | 63 |
| interactions | 32 | 8 | 40 | – | – | – |
| resolve | 32 | 7 | 39 | – | – | – |
| clinical | 66 | 19 | 85 | 66 | 19 | 85 |
| follow-up | 50 | 8 | 58 | 34 | 10 | 44 |
| accept-set | 21 | 5 | 26 | 11 | 4 | 15 |
| tool-only | – | – | – | 29 | 5 | 34 |
| **all** | **308** | **76** | **384** | **330** | **89** | **419** |

- The API translation tier is 116 tasks written for the API (13 curated, 103 generated) plus 62 twins of MVS translation tasks. The API grounded tier is twins only.
- Paraphrases (all public): api clinical 10; api followup 4; api grounded 8; api tool_only 8; api translation 8; mvs clinical 10; mvs followup 6; mvs grounded 8; mvs interactions 8; mvs resolve 8; mvs translation 4.
- 129 templates ("families"). Largest template share per track and tier: api accept_set `acc-chain-colours` 3 of 15 (20%); api clinical `clin-pair-target` 10 of 85 (12%); api followup `fu-add-residue` 4 of 44 (9%); api grounded `gr-catalytic` 6 of 63 (10%); api tool_only `api-canvas` 4 of 34 (12%); api translation `api-hide` 11 of 178 (6%); mvs accept_set `acc-chain-colours` 3 of 26 (12%); mvs clinical `clin-pair-target` 10 of 85 (12%); mvs followup `fu-add-residue` 4 of 58 (7%); mvs grounded `gr-catalytic` 6 of 63 (10%); mvs interactions `in-ca-distance` 5 of 40 (12%); mvs resolve `res-name` 12 of 39 (31%); mvs translation `tr-colour-by-chain` 5 of 73 (7%).

Where the files are:

| directory | what | written by |
|---|---|---|
| `tasks/mvs_generated` | MVS translation | `scripts/generate_mvs_tasks.py` |
| `tasks/mvs_grounded` | MVS grounded | `scripts/generate_grounded_tasks.py` |
| `tasks/mvs_interactions` | MVS interactions | `scripts/author_interaction_tasks.py` |
| `tasks/mvs_resolve` | MVS resolve | `scripts/generate_resolve_tasks.py` |
| `tasks/mvs_clinical`, `tasks/api_clinical` | clinical, both tracks | `scripts/generate_clinical_tasks.py` |
| `tasks/mvs_followup`, `tasks/api_followup` | follow-up turns | `scripts/generate_followup_tasks.py` |
| `tasks/mvs_accept`, `tasks/api_accept` | accept-set | `scripts/generate_accept_set_tasks.py` |
| `tasks/api_calling`, `tasks/api_generated` | API translation and tool-only | `scripts/generate_api_tasks.py` |
| `tasks/api_twins` | API twins of MVS translation and grounded tasks | `scripts/translate_mvs_to_api.py` |
| `tasks/paraphrases` | terse and indirect phrasings | `scripts/generate_paraphrases.py` |

## Structures

- **78 structures** are used, of the frozen panel of 79 (`data/panel`). Not used: 1HSG (1HSG is the API prompt's worked example).
- **Reuse.** Within one tier of one track no structure is in more than 6 tasks (reached by api clinical 2HHB, api clinical 8C86, mvs clinical 2HHB, mvs clinical 8C86). Over the whole corpus (both tracks, all tiers, paraphrases not counted) the most used are 2HHB, 8C86 with 22 tasks each; the least used are 1L2Y, 1UBQ, AF-P61626-F1-MODEL_V6 with 2.
- 3 API tasks name no single structure (`api-005`, `api-superposition-p00740`, `api-superposition-p10275`).
- **Held back: 15 structures**, one list for the whole corpus (`data/panel/heldback.json`): 1EHZ, 1FS3, 1IGT, 1LMB, 1RX2, 2C9V, 2OMF, 2PTC, 3KCG, 5NI1, 6HPO, 6TC2, 6THA, 8CE0, 8K7F. Public tasks on a held-back structure: 0. 165 original tasks are held back (20%).

## Special kinds

- **Twins.** 261 of the 384 MVS tasks (68%) have an API twin with the same prompt and the same target atoms: accept-set 15, clinical 85, follow-up 36, grounded 63, translation 62. 125 of them were written by the translator; 18 of those set a hide toggle (`provenance.difficulty.context_switched_off`), and 6 of these also accept the list without it, because the request never asks for anything to be hidden. MVS tasks without a twin: accept-set 11, follow-up 22, interactions 40, resolve 39, translation 11.
- **Unstated attributes.** 112 API tasks outside the accept-set tier list accepted call forms for what their request leaves open (`scripts/api_forms.py`): cartoon style set: 1; default view, rest in the backdrop colour: 105; default view, rest untouched: 80; nothing hidden: what the request does not name is drawn too: 6. On the MVS track the grader does it: 20 single-turn references draw something with no colour node, and there any colour is right.
- **Paraphrases.** 30 requests (a twin pair is one request), seeded, public split only (0 held back), none of an accept-set task (0); each has the full, a terse and an indirect phrasing, written by hand and checked by rule. 82 new task files.
- **Follow-ups.** 58 MVS and 44 API two-turn tasks (36 twinned). 10 MVS and 8 API are "no change" tasks, where the start state returned unchanged is the right answer (already true: 16, not expressible in the format: 2; none is a question).
- **Accept-set.** 26 MVS and 15 API tasks where the request leaves one countable thing open. They hold 87 MVS and 43 API *readings* (`provenance.accepted_states`); as final states, counting API call forms, 87 and 92. The paper counts readings. Besides these, 242 other tasks list accepted alternatives and are not accept-set tasks: API call forms (unstated attributes): 112; API clinical twins: the residue's own stretch of cartoon: 85; other equivalents an API generator lists: 9; resolve: other namings of the same drawing: 36.
- **Clinical tier** (85 tasks per track, 27 proteins, 33 structures, 8 of them held back):
  - target residue's author number differs from its UniProt number: **60 of 85** (71%);
  - target's author chain id differs from its label chain id: **25 of 85** (29%);
  - a target has an insertion code: **1 of 85** (1%);
  - an answer that uses the number in the variant name as the author residue number is right: **37 of 85** (44%);
  - 14 names are in mature-protein numbering;
  - offset pairs (the same variant on a structure whose author numbers differ from UniProt and on one numbered as UniProt): CALM1 1, CRYGD 1, HBB 4, LYZ 1 (4 proteins); mature-numbering pair: HBB 1; no-offset control pairs: TP53 2; pairs with one side held back: 0;
  - 10 tasks per track (`clin-sse-helix`, `clin-sse-strand`) are flagged `provenance.clinical.report_apart`: they need the entry's own helix or strand records, which only the grounding pack states, and are reported apart from the tier.

## Two example tasks per tier

**Translation**
- `tr-colour-by-chain-1aoi`: "Load 1AOI and show it as a cartoon coloured by chain."
- `tr-nucleic-1aay`: "1AAY, cartoon: DNA khaki, protein salmon."

**Grounded**
- `gr-catalytic-1aki-p00698`: "1AKI: grey cartoon, with the two catalytic residues drawn as green ball-and-stick."
- `gr-disulfides-1crn`: "1CRN: grey cartoon, with every disulfide-bonded cysteine drawn in plum ball-and-stick."

**Interactions**
- `in-ca-distance-1ake`: "Show 1AKE as a yellow cartoon. Add a distance measurement (dashed line with the value as label) from the CA atom of Ser183 to the CA atom of Lys200. Both residues are in chain B."
- `in-computed-1a6m-hem`: "1A6M: grey cartoon; heme as red ball-and-stick with its computed non-covalent interactions shown; camera on the heme."

**Resolve**
- `res-name-p00004`: "Find a PDB entry of horse heart cytochrome c and show it as a yellow cartoon."; 2 accepted alternative(s)
- `res-gene-p01009`: "Find a PDB entry of human SERPINA1 and show it as a brown cartoon."; 2 accepted alternative(s)

**Clinical**
- `clin-pair-target-calm1-6m7h-e141k-mvs`: "Using PDB entry 6M7H, show as red spacefill spheres the wild-type residue at the position of the CALM1 (Calmodulin-1, UniProt P0DP23) missense variant p.Glu141Lys (pathogenic in ClinVar)."
- `clin-pair-context-crygd-1hk0-s52p-mvs`: "PDB entry 1HK0: the CRYGD (Gamma-crystallin D, UniProt P07320) variant p.Ser52Pro is classified as likely pathogenic in ClinVar. Show the whole structure as a white cartoon, with the residue it replaces as green spacefill spheres."

**Follow-up**
- `fu-add-residue-2hhb-mvs`: "Now draw His122 of chain A as ball-and-stick too, in yellow; the cartoon keeps its colour."; with a start state
- `fu-recolour-ligand-1hvr-mvs`: "Could you turn the ligand XK2 blue?"; with a start state

**Accept-set**
- `acc-chain-colours-1aay-mvs`: "Load 1AAY and show it as a cartoon, with the three chains coloured green, magenta and cyan."; 5 accepted alternative(s)
- `acc-metal-copy-1tup-mvs`: "Show 1TUP with the protein and DNA as a cartoon and the zinc ion as a spacefill sphere, coloured magenta."; 3 accepted alternative(s)

**Tool-only**
- `api-005`: "Open the PDBe-KB superposition view for human haemoglobin subunit alpha (UniProt P69905) on a white background."
- `api-006`: "Show insulin (4INS), hide the waters and the heteroatoms, set glossy lighting, and make it slowly spin."

## Rulings applied (FINAL_PLAN.md, "Rulings after the corpus merge", 2026-11-15)

| ruling | what was done | where |
|---|---|---|
| Unstated attributes are free | **MVS:** a grader rule. A single-turn reference with no colour node on a drawing takes any colour in the answer, except a colour the reference states for other atoms in the same representation type; follow-ups keep every colour of the start scene. An unstated representation is listed as accepted scenes (`acc-representation-open`). **API:** accepted call forms, written by one module for every generator: the cartoon by the viewer's default or by the style; nothing hidden that the request never names; the stretch of cartoon under an added representation. | `molbench/drawn.py`, `molbench/mvs.py`, `scripts/api_forms.py`, `GRADING.md` ("Unstated attributes are free") |
| Tier sizes stay as built | No tier was trimmed. Sizes moved only through the rulings below: five tasks per track from grounded to translation, six clinical tasks per track for the offset pairs, ten new API translation tasks. | table above |
| No-lookup tasks belong to the translation tier | `gr-nucleic` ("the DNA", Mol\*'s own `nucleic` selection) is now `tr-nucleic`, five tasks and their twins. It keeps its place in the grounded generator's order, so no other grounded task changed. | `scripts/generate_grounded_tasks.py` (`MOVED_TO_TRANSLATION`) |
| Question prompts are not no-change tasks | `fu-noop-question` is replaced by `fu-noop-ligand-rep`: the ligand asked for as ball-and-stick, which it already is. | `scripts/generate_followup_tasks.py` |
| "Main ligand" is a biological ligand | One list of what is not one: crystallisation additives, buffers and salts, detergents and lipids, a heavy-atom reagent (30 component codes, each with what it is). The follow-up, accept-set, translation and API generators read it. Tartrate (1D5R), the detergent of 2OMF, the PEG fragment of 6THA and the lipids of 1C3W and 1K4C are no longer anybody's "ligand". | `data/corpus/additives.json`, `scripts/additives.py` |
| Undo tasks must not pass on the last step alone | The three `api-undo` variants whose undo changed nothing (the viewer replaces highlights, tooltips and colouring anyway) are rewritten: two tooltips set and one removed; two things coloured and one colour taken off; a colour kept while a highlight is cleared. Every undo task carries the trap "every step but the undo", which must fail. A list that never does the undone thing ends in the same state and is right: that is what final-state grading means. | `scripts/generate_api_tasks.py` (`UNDO_SKIPPED`) |
| Helix/strand clinical tasks reported apart | `provenance.clinical.report_apart` on the ten tasks per track. | `scripts/generate_clinical_tasks.py` |
| Offset comparison on more than one protein | Offset pairs now rest on four proteins: HBB, LYZ, CRYGD, CALM1. The AlphaFold models of the last three joined the panel as the no-offset side (free download, frozen; atom and SIFTS tables built; `public_only`, so the held-back list is unchanged). TTR has no pair: 8C86 already carries the tier's maximum of six tasks. | `data/panel/seed.json`, `scripts/build_panel.py`, `scripts/generate_clinical_tasks.py` (section G) |
| Contested examples not featured | APOE R158C (R176C in UniProt numbering) is in `NOT_USED` and no task asks about it; APOE is no longer in the featured list. | `scripts/generate_clinical_tasks.py` |
| No pair across the split | The HBB pair on held-back 5NI1 moved to 1HHO. Every pair is public on both sides. | same |
| Paraphrases: never accept-set, natural English | 30 seeded public requests, none from the accept-set tier. The mechanical rewrite is gone; each terse and indirect wording is written by hand and a rule fails the build if it drops an id, a number, a code, a chain letter, a quoted text, a colour or a representation. | `scripts/generate_paraphrases.py` (`WORDINGS`, `lost`) |
| Known oddities | `api-uniprot-residue-1d3z` ("Ile621 of P0CG48") is replaced: no UniProt-numbered task on a tandem-repeat UniProt entry. The `api-undo` tasks: above. | `scripts/generate_api_tasks.py` (`REPEAT_PROTEINS`) |
| API surface never used | `api-inscode` (5): a residue with an insertion code, which the viewer can only name by label chain and label number. `api-label-chain` (5): a chain named by its label chain id where that is not the author's. | `scripts/generate_api_tasks.py` |

### Accept-set wording (the integrator's item 11): decided

- **Residue templates keep the bare name and number** ("Colour Ile66 blue"), with no protein
  named. Which copy is meant is exactly what the task leaves open; accepted is the residue
  in any one chain, or in every chain.
- **"Show the heme in green" accepts every representation type that draws the whole
  ligand** (ball-and-stick, spacefill, line, surface). The request states none, and an
  unstated attribute is free. Two drawings at once are still one too many.
- **"The calcium ion" in 8EPH** (four ions, two copies of the complex): accepted is any one
  ion, all four, and now also the two ions of one copy of the complex, read from the
  entry's assemblies. Two ions from different copies are no reading.
- **Mol\*'s built-in `ligand` selection** is accepted where the request says "the ligand"
  (it is the viewer's word for what was asked), and not where the request names a compound
  ("the heme"): there the bonded protein residues it adds were not asked for.
- **Counting.** The paper counts readings, not call forms (the numbers are above), and
  does not count tasks that merely list namings or call forms under `accepted`.

## Tasks dropped or replaced in this pass

- `gr-nucleic-*` (5 + 5 twins) are `tr-nucleic-*` now: same requests, other tier and id.
- `fu-noop-question-*` (2 per track) replaced by `fu-noop-ligand-rep-*`. The main-ligand rule
  moved follow-ups off TLA, C8E, P33, LI1 and DGA; 34 follow-up files per the generator's
  seeded order changed structure or wording.
- `api-undo-1f88`, `-8k7f`, `-9f69` rewritten (same ids, new requests); `api-undo-1rx2` kept.
- `api-uniprot-residue-1d3z` replaced; five other API files moved to another structure as the
  seeded order shifted (`api-entity-1igt` to 5UAK, `api-style-colour-1iro` to 1D3Z,
  `api-uniprot-range-6m7h`, two `api-alphafold` tasks to the new models).
- Clinical: `clin-legacy-target-apoe-8ce0-r176c` and `clin-multi-context-apoe-8ce0-l46p-r154s-a170p`
  replaced by other APOE variants; the pair `clin-pair-context-hbb-5ni1-f43s` / AlphaFold
  replaced by `...-hbb-1hho-r31t`; three new pairs (LYZ W82R, CRYGD S52P, CALM1 E141K).
- `acc-representation-open-1hrc` replaced by `...-3k34` (3K34 has one biological ligand now
  that its glycerol and mercury reagent are not counted).
- All 88 old paraphrases are replaced by 82 new ones (44 old originals, four of them
  accept-set; 41 now).

## Checks run on this state (2026-11-16)

| check | result |
|---|---|
| every generator with `--check` (eight), translator `--all --check`, paraphrases `--check`, `build_grounding_packs.py --check`, `build_panel.py --check` | all up to date; 79 panel entries checked, 0 bad |
| `scripts/validate_tasks.py --final` | OK: every check passed (885 tasks, 0 old-format) |
| `scripts/check_api_refs.py --cif` (offline, all 458 API task files) | all checks passed |
| `check_api_refs.py --viewer --sample 60 --seed 20261116 --no-probes` | 153 call lists (references and accepted forms) run in pdbe-molstar 3.3.2, 396 selections compared atom for atom, all agree; 1 list skipped (settings only) |
| `check_api_refs.py --viewer --no-probes --only` every API task file changed or added since the merge (277 files) | 705 call lists run in pdbe-molstar 3.3.2, 1,645 selections compared atom for atom, all agree; 0 lists skipped (settings only) |
| `generate_mvs_tasks.py --check --viewer` (translation tier, with `tr-nucleic`) | 76 scenes of 73 tasks loaded in Mol\* 5.9.0; 0 differ |
| `generate_followup_tasks.py --check --viewer` | 106 scenes drawn in Mol\*, 0 differ; 76 call lists in pdbe-molstar, 181 selections, 0 differ |
| `generate_accept_set_tasks.py --check --viewer` | 87 MVS states loaded in Mol\* 5.9.0, 0 differ |
| `build_atom_tables.py --verify --check` on the 15 component selectors of the 10 new clinical MVS references (9 structures, four of them AlphaFold models) | exit 0, every selector agrees with Mol\*; the rebuilt tables are byte-identical |
| `scripts/grader_controls.py --check` | up to date; MVS 1,090 controls on 78 entries, API 910 on 69: 0 false passes, 0 false fails |
| `uv run pytest -q` | 2,696 passed |

Not re-run in this pass: the manifest dry run and its cost projection (the runner is
being changed in another worktree; the corpus is 16 task files larger than at the merge,
so the projection there is about 2% low), `grader_controls.py --viewer` (the two new
"equivalent" control kinds cannot be read back from the viewer by construction: the
viewer shows two colours where the request states none), and the 40-reference Mol\*
read-back of the MVS core tiers, whose task files did not change apart from `tr-nucleic`.

## Known weaknesses

- **Unstated attributes on the API track are an enumerated list, not a grader rule.** The
  accepted forms cover what the call format gives naturally (style or default view,
  backdrop by `non_selected_color` or by naming the chains, hide toggles left out, the
  three natural colours of the stretch under an added representation). An answer that
  paints an unmentioned component in some other colour, or reaches the picture by another
  mix of toggles, is still graded as wrong. A form is not offered where the viewer's own
  default drawing of the requested atoms would stay visible in another type (sugars keep
  their 3D-SNFG symbols), where the request is "only chain A" or "nothing else", or
  where the reference had to hide and redraw the polymer (three twins: `gr-attachment-1hrc-hec`,
  `gr-secstruct-3ert`, `tr-het-code-3ert`).
- **Twins are not graded by the same leniency.** An MVS answer that draws something the
  request does not name loses success (decision 18); the API twin accepts the default
  view, which draws water and other ligands. The paired analysis should say so, and its
  sensitivity check (twins without an unstated hide toggle) is still needed for the 12
  twins that keep one.
- **The budget** was not re-projected (see above).
- **Tier sizes are above the plan** in places, by ruling: translation 73 MVS, grounded 63,
  accept-set 26 + 15, clinical 85.
- **Held-back share is uneven**: 8 of the 33 clinical structures and 4 of the 15 API
  accept-set tasks, against about a fifth elsewhere.
- **Offset pairs outside HBB are one per protein** (LYZ, CRYGD, CALM1), and their no-offset
  side is always an AlphaFold model, so "no offset" and "predicted model, named by a file
  URL on the API track" are confounded there. TTR could not get a pair without exceeding
  six tasks on 8C86.
- **The 10 clinical helix/strand tasks** need the entry's own annotation, which only the
  grounding pack states: flagged, to be reported apart.
- **Paraphrase wordings were written and read by one author** and checked by rule for
  dropped values, not by a structural biologist. A new seeded selection needs new
  wordings before the script will run.
- **The additive list is hand-written** from the panel's components and common PDB
  additives; a new panel entry may bring a component nobody has classified.
- **`api-undo` tests the undo only in one direction**: skipping the undo fails, but a list
  that never does the undone step passes, as final-state grading implies.
- **Grader limits that shape scores**: the target score ignores a missing distance line;
  a second coloured cartoon on a recoloured range fails success on the MVS track; ball-and-stick
  for a lone ion scores target 0; lines, labels and camera focus are not read back from Mol\*.
- **Not exercisable in the headless viewer** (graded as declared settings only):
  AlphaFold view, domain / validation / symmetry annotation, maps, sequence panel,
  lighting, superposition, ligand view.
- **Not computed yet** (runner and paper tables): the preserved score of follow-ups
  (`provenance.preserved`), the three-way outcome for made-up PDB ids, one vocabulary for
  the difficulty keys of the generators.
- **Left as found**: `in-metal-contact-1plc-cu` omits Met92 (the prompt names its three
  residues); `res-name-p00299` accepts isoform A only.

## Rebuild order

```bash
uv run python scripts/generate_grounded_tasks.py   # before generate_mvs_tasks.py, which takes tr-nucleic from it
uv run python scripts/generate_mvs_tasks.py        # then author_interaction_tasks.py, generate_resolve_tasks.py
uv run --extra authoring python scripts/generate_clinical_tasks.py
uv run python scripts/generate_api_tasks.py
uv run python scripts/generate_followup_tasks.py
uv run python scripts/generate_accept_set_tasks.py
uv run python scripts/translate_mvs_to_api.py --all
uv run python scripts/generate_paraphrases.py      # the recorded selection
uv run python scripts/translate_mvs_to_api.py --all   # refreshes the twin README counts
uv run python scripts/build_grounding_packs.py --check
uv run python scripts/grader_controls.py --check
uv run python scripts/validate_tasks.py --final
uv run python scripts/corpus_report.py             # this file
```

All generators read `data/panel/heldback.json` and `data/corpus/additives.json`. A
rebuild of the translation and grounded tiers keeps the twin links already in the files.
A panel entry added after the held-back list was frozen is marked `public_only` in
`data/panel/seed.json`.
