# The MolBench corpus (integration state, 2026-11-15)

**Not frozen yet.** The manifest still says `corpus-v1.0-dev` and the hash is not pinned;
the lead freezes after review. Hash of `tasks/` on disk at this state:
`ef851e529f43d3abd781bc0ad9a35f2d2b4e0b73cb49538d5f05e1716c137feb`.

Every number below was counted from the task files through `molbench.tasks.load_corpus()`.
Format: `TASK_FORMAT.md`. Grading: `GRADING.md`. Each tier directory has its own generated
`README.md` with templates and how each reference is derived.

## Size

869 task files: **781 original tasks** (378 MVS, 403 API) and **88 paraphrases** of 44 of them.

Original tasks by track, tier and split (public / held back):

| tier | MVS public | MVS held back | MVS total | API public | API held back | API total |
|---|---:|---:|---:|---:|---:|---:|
| translation | 51 | 17 | 68 | 127 | 36 | 163 |
| grounded | 56 | 12 | 68 | 56 | 12 | 68 |
| interactions | 32 | 8 | 40 | – | – | – |
| resolve | 32 | 7 | 39 | – | – | – |
| clinical | 59 | 20 | 79 | 59 | 20 | 79 |
| follow-up | 47 | 11 | 58 | 34 | 10 | 44 |
| accept-set | 21 | 5 | 26 | 11 | 4 | 15 |
| tool-only | – | – | – | 29 | 5 | 34 |
| **all** | **298** | **80** | **378** | **316** | **87** | **403** |

- The API translation tier is 106 tasks written for the API (13 curated, 93 generated) plus
  57 twins of MVS translation tasks. The API grounded tier is twins only.
- Paraphrases (all public): MVS 48 (translation 4, grounded 8, interactions 8, resolve 8,
  clinical 8, follow-up 4, accept-set 8); API 40 (translation 6, grounded 8, clinical 8,
  follow-up 4, accept-set 8, tool-only 6).
- 127 templates ("families"). Largest template share per tier: at most 12%, except
  resolve (`res-name` 31%: there are only five ways to name a protein) and the 15-task API
  accept-set tier (five templates of three, 20% each).

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

- **75 structures** are used, all from the frozen panel of 76 (`data/panel`). The one panel
  entry not used is 1HSG, the API prompt's worked example.
- **Reuse.** Within one tier of one track no structure is in more than 6 tasks (reached only
  in the clinical tier, by 2HHB and 8C86). Over the whole corpus (both tracks, all tiers,
  paraphrases not counted) the most used structures are 8C86 and 2HHB with 22 tasks each;
  the least used are 1UBQ and 1L2Y with 2.
- Three API tasks name no single structure (two superposition tasks and `api-005`).
- **Held back: 15 structures**, one list for the whole corpus (`data/panel/heldback.json`):
  1EHZ, 1FS3, 1IGT, 1LMB, 1RX2, 2C9V, 2OMF, 2PTC, 3KCG, 5NI1, 6HPO, 6TC2, 6THA, 8CE0, 8K7F.
  No held-back structure is in any public task. 167 original tasks are held back (21%).

## Special kinds

- **Twins.** 255 of the 378 MVS tasks (67%) have an API twin with the same prompt and the
  same target atoms: translation 57, grounded 68, clinical 79, follow-up 36, accept-set 15.
  125 of them were written by the translator; 18 of those 125 need a hide toggle the
  request never states (`provenance.difficulty.context_switched_off`).
- **Paraphrases.** 30 requests (a twin pair is one request), seeded, public split only,
  spread over all eight tiers; each has the full, a terse and an indirect phrasing. 88 new
  task files. Four requests use hand-written templates (accept-set); 26 use the mechanical
  rewrite (marked `generic` in `tasks/paraphrases/README.md`).
- **Follow-ups.** 58 MVS and 44 API two-turn tasks (36 twinned). 10 MVS and 8 API are
  "no change" tasks, where the start state returned unchanged is the right answer.
- **Accept-set.** 26 MVS and 15 API tasks where the request leaves one countable thing
  open and several final states are right. Besides these, 128 other tasks list accepted
  alternatives: 79 API clinical twins, 36 resolve tasks (other namings of the same
  drawing), 13 translation and tool-only tasks.
- **Clinical tier** (79 tasks per track, 27 proteins, 30 structures):
  - target residue's author number differs from its UniProt number: **57 of 79 (72%)**;
  - target's author chain id differs from its label chain id: **23 of 79 (29%)**;
  - one target has an insertion code; 14 names are in mature-protein numbering;
  - an answer that uses the number in the variant name as the author residue number is
    right in 34 of 79, so the paper should stratify on that.

## Tasks dropped, and why

- **All 70 old MVS tasks** (5 hand-written, 36 translation, 8 grounded, 6 interactions,
  6 resolve, 9 clinical) are replaced by generated tasks on the panel. The old clinical
  tasks named variants ClinVar now calls Conflicting. The October copies are frozen in
  `data/october/tasks` so the October numbers still reproduce.
- **2 visual-rubric tasks** moved to `tasks_future/` (out of this paper, decision 8).
- **123 MVS tasks have no API twin**: 39 resolve tasks (entries outside the panel are
  accepted and have no atom table), 30 with a distance line, 5 colour-by-chain themes,
  5 computed-interaction requests, 5 with transparency, 4 with text labels, 2 with a
  representation the API lacks, and 33 follow-up or accept-set tasks that their own
  generator left on one track on purpose.
- **Not built:** switch-structure follow-ups (the task format refuses a start state on
  another structure); clinical requests on an unresolved position, on ligand contacts,
  or with "hotspot" wording; ambiguous requests that are a judgement and not a count
  ("clean up the view"); sequence-motif, within-5-Å and property selections.
- **Replaced during review:** `gr-metal-site-1plc-cu` (the reference left out Met92) by
  `gr-metal-site-6m7h-ca`.
- **Changed at integration:** the accept-set tier holds back a fifth of its own tasks, so
  under the shared held-back list 8 of its tasks moved to other structures.

## Checks run on this state

| check | result |
|---|---|
| every generator with `--check` | all eight up to date; translator and paraphrases too |
| `scripts/validate_tasks.py` and `--final` | OK: every check passed (869 tasks, 0 old-format) |
| `scripts/check_api_refs.py --cif` (offline, all 443 API task files) | all checks passed |
| `check_api_refs.py --viewer --sample 80 --seed 20261115 --no-probes` | 137 call lists run in pdbe-molstar 3.3.2, 224 selections compared atom for atom, all agree; 3 lists skipped (settings only) |
| `build_atom_tables.py --verify --check` on 40 seeded MVS references (65 selectors, 31 structures) in Mol* | exit 0, every selector agrees |
| `scripts/grader_controls.py --check` | up to date; MVS 1,030 controls, API 850: 0 false passes, 0 false fails |
| `uv run pytest -q` | 2,580 passed |
| manifest dry run | every check passes **except the budget**: see below |

**Dry-run cost projection** (3 samples, 4 conditions, 869 tasks, 122,172 calls):
core panel **$181.74** expected (cap $120.00); optional models $501.30; total $683.03.
The run would refuse to start as the manifest stands. Without the structured-output
condition the core panel would be about $106.

## Known weaknesses

- **The budget does not fit** (above). Corpus size, samples, conditions or the cap has to
  change before the paid run.
- **Tier sizes are above the plan** in places: translation and grounded 68 each (plan ~60),
  accept-set 26 + 15 (plan ~15), clinical 79 (plan ≥ 40).
- **One clinical pair straddles the split**: HBB F43S on the AlphaFold model (public) and
  on 5NI1 (held back). The other six pairs are in one split.
- **Held-back share is uneven**: 8 of the 30 clinical structures and 4 of the 15 API
  accept-set tasks, against about a fifth elsewhere.
- **Offset pairs exist for one protein only** (HBB, five pairs); the two TP53 pairs are
  no-offset controls.
- **The 10 clinical helix/strand tasks** need the entry's own annotation, which only the
  grounding pack states. Expect task success near 0 without the pack.
- **Twins can be harder than their MVS partner for a format reason**: 18 translator twins
  need unstated hide toggles. The paired analysis should report twins with and without.
- **API clinical twins** fail success if `color` is omitted on the residue (the viewer
  paints that cartoon stretch orange). The prompt's reference text says so.
- **Generic paraphrases are clumsy** (26 of 30 requests): information is kept, but terse
  forms read like "Find PDB entry human SERPINA1, it brown cartoon". Read them before
  the freeze.
- **Grader limits that shape scores**: the target score ignores a missing distance line;
  a second coloured cartoon on a recoloured range fails success; ball-and-stick for a
  lone ion scores target 0; lines, labels and camera focus are not read back from Mol*.
- **Not exercisable in the headless viewer** (graded as declared settings only):
  AlphaFold view, domain / validation / symmetry annotation, maps, sequence panel,
  lighting, superposition, ligand view.
- **Not computed yet**: the preserved score of follow-ups (`provenance.preserved`) and the
  three-way outcome for made-up PDB ids; neither is wired into the runner or the tables.
- **Difficulty key names differ between generators** (`needs_numbering_offset`,
  `numbering_offset`, …). The paper tables need one map.
- **Several clinical variants rest on ClinVar records without assertion criteria**
  (for example APOE R158C, the common ε2 allele, called pathogenic).
- **Prompt naturalness** has been read by builders and reviewers only, not by a
  structural biologist.

## Rebuild order

```bash
uv run python scripts/generate_mvs_tasks.py        # then generate_grounded_tasks.py,
                                                   # author_interaction_tasks.py, generate_resolve_tasks.py
uv run python scripts/generate_clinical_tasks.py
uv run python scripts/generate_api_tasks.py
uv run python scripts/generate_followup_tasks.py
uv run python scripts/generate_accept_set_tasks.py
uv run python scripts/translate_mvs_to_api.py --all
uv run python scripts/generate_paraphrases.py      # the recorded selection
uv run python scripts/translate_mvs_to_api.py --all   # refreshes the twin README counts
uv run python scripts/validate_tasks.py --final
```

All generators read `data/panel/heldback.json`. A rebuild of the translation and grounded
tiers keeps the twin links already in the files.

## Two example tasks per tier

**Translation**
- `tr-chains-named-4ins` — "Load 4INS as a cartoon and colour chain A magenta, chain B cyan,
  chain C plum and chain D red." Reference: one cartoon, the four author chains in the four colours.
- `tr-het-code-3ert` — "3ERT: grey cartoon, and the het group OHT as lime green
  ball-and-stick." Reference: grey polymer cartoon plus component OHT as lime green ball-and-stick.

**Grounded**
- `gr-attachment-1hrc-hec` — "Load 1HRC; show the protein as a grey cartoon, the heme as teal
  ball-and-stick, and the cysteines it is covalently attached to as brown ball-and-stick."
  Reference: Cys14 and Cys17 of chain A, read from the entry's link records.
- `gr-ligand-1stp-btn` — "In 1STP, draw the protein as a grey cartoon and pick out the biotin
  in green ball-and-stick." Reference: component BTN, found from the frozen component names.

**Interactions**
- `in-hbond-1iep` — "1IEP: grey cartoon; Asn322 and Asp325 as green ball-and-stick; measure the
  hydrogen bond between ND2 of Asn322 and OD2 of Asp325 with a labelled dashed line; focus the
  camera on these two residues. Both residues are in chain B." Reference: the two residues, a
  distance line between the two atoms (2.67 Å in the structure), and a focus.
- `in-ca-distance-9fb2` — "9FB2, hot pink cartoon; how far apart are the C-alpha atoms of Pro189
  and Phe436? Draw the distance as a labelled dashed line." Reference: cartoon plus a line
  between the two CA atoms of chain A.

**Resolve**
- `res-dna-p04637` — "Show me a structure of human p53 bound to DNA: the protein as a cyan
  cartoon and the DNA as a lime green cartoon." Reference: 1TUP; the same drawing on any
  other entry on the frozen accepted list is also right.
- `res-gene-p01112` — "Show me a structure of the protein encoded by the human gene HRAS, as a
  blue cartoon." Reference: a blue polymer cartoon on any accepted HRAS entry.

**Clinical**
- `clin-chain-ttr-8c86-g87r-chaina-mvs` — "In PDB entry 8C86, show the residue replaced by the
  likely pathogenic TTR (Transthyretin) variant G87R (ClinVar) as green ball-and-stick in
  chain A only (author chain ID)." Reference: author chain A, author residue 67 (UniProt 87
  minus 20). The API twin selects UniProt P02766 position 87 in author chain A.
- `clin-legacy-context-crygd-1hk0-r37p-mvs` — "In PDB entry 1HK0, show the whole structure as a
  gray cartoon and the residue replaced by the likely pathogenic CRYGD (Gamma-crystallin D)
  variant R36P (ClinVar) as yellow spacefill spheres. The name R36P is in mature-protein
  numbering: residues are counted from the first residue of the mature protein, that is, after
  the initiator methionine." Reference: grey cartoon of everything plus residue 36 (UniProt 37).

**Follow-up**
- `fu-referent-colour-5cj6-mvs` — start: a scene with one magenta chain; request: "Make the
  magenta chain plum." Reference: the start scene with chain B plum and everything else unchanged.
- `fu-noop-shown-1f88-api` — start: 1F88 loaded in the default view with coloured chains and
  ligand; request: "Cartoon for the protein, please." Reference: the start calls unchanged (the
  protein is already a cartoon).

**Accept-set**
- `acc-residue-colour-4ins-mvs` — "Show 4INS with the protein as a cartoon. Colour Lys29
  yellow." Accepted: Lys29 of chain B, of chain D, or of both.
- `acc-ligand-which-2cpp-mvs` — "Open 2CPP with the protein as a cartoon and the ligand in
  orange ball-and-stick." Accepted: camphor, the heme, both, or the viewer's own `ligand` selection.

**Tool-only (API)**
- `api-maps-3ert` — "Load 3ERT with its electron-density maps, drawing the positive Fo-Fc
  difference map as a wireframe at opacity 0.7." Reference: `load`, `load_maps` on, then
  `map_settings` for the positive Fo-Fc map.
- `api-canvas-1udt` — "Load 1UDT on a black background with glossy lighting and set it
  spinning." Reference: `load`, then background, lighting and spin settings.
