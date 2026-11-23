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

## Audit of 2026-11-16 (four independent audits) and what was done

Four audits (structural biologist, clinical geneticist, benchmark methodologist, adversarial
grader tester) graded hand-written answers and re-derived references. No reference residue
was found wrong. Every finding below was reproduced before it was acted on; each fix is in a
generator, a grader or a prompt, and `tests/test_audit_fixes.py` pins it.

| finding | verdict | what was done |
|---|---|---|
| API: the prompt's own example form (residue stretch in the highlight colour) failed on 45 twins | real | `api_forms.py` adds the form wherever the request states the backdrop; control kind `unstated_stretch_in_highlight_colour` |
| API: 7 tasks accepted a view that draws what the request excludes ("no sugars", "only the DNA") | real | `provenance.excludes`; every default-view form carries the hide toggle; a build check and a test forbid an accepted form that draws the excluded component |
| API: UniProt keys on an AlphaFold model scored 0 (10 tasks, the no-offset side of the offset pairs) | real | `sifts.frozen_name`; AlphaFold references use the UniProt keys; control kind `uniprot_number_on_alphafold_model` |
| MVS prompt's worked example used the selector `ligand` for a named compound, on a panel structure | real | example is on 1HSG with the compound by its code; a test grades it and checks 1HSG is in no task |
| Task success is not the same test on the two tracks (135 of 225 pairs) | real, by design (decisions 17, 18) | paired analysis is on the target score first, task success second; said in the paper |
| Clinical: variants confirmed only by another gene's record (43), by a haplotype (37) or without assertion criteria (246) | real | `data/panel/clinvar_records.json`; a variant needs a record of its own; APOE R154S and CA2 K18E named as not used; CA2 and TPI1 have no task; LYZ I74T kept by name |
| Clinical: one-letter names in UniProt numbering looked like mature numbering (25 tasks) | real | such names carry `p.`; GCK and PRSS1 by their usual names |
| Clinical: pooled classification wording, no snapshot date, stale README sentence | real | wording from the variant's own record; date in the tier README |
| API: three twins failed their plain answer (residue with no trace atom) | real | the replay draws cartoon only on residues with a trace atom; the three twins are plain again |
| API: default-view ruling applied unevenly (tr-chains-named, api-017, api-018, clin-sse, gr-entity by author id, spheres over a ligand) | real | forms added in `api_forms.py`; a corpus test over every request that says "cartoon" |
| API: an unrequested `hide_water` on an accepted default view failed 157 of 175 tasks | real | `free_hide` (a grader rule) on the 146 tasks that accept both the cartoon style and the default view; elsewhere it stays an unrequested change (135 of 302 tasks probed still fail it, with target score 1) |
| MVS: download source and parse format were not graded | real | a URL that names no structure file, or a format that is not the file's, is `load_failed`, score 0 |
| `api-inscode` (5 tasks) could not be answered from the request | real | the prompt states the label chain and number; the API reference says `auth_ins_code_id` is ignored |
| Reply parser: a huge integer or very deep nesting crashed grading | real | `invalid_json`; a bracket in the prose no longer hides the answer |
| Follow-ups without a target: the unchanged start state had target score 1 (13 tasks) | real | no target score on those tasks |
| Grounded: named ligand missing from the target; helix and secondary-structure tasks not flagged | real | ligand is a target part; `report_apart` on `gr-longest-helix` and `gr-secstruct` |
| Resolve: a correct chain-id answer on another accepted entry scores 0 (3 of 5,739 accepted entries have an atom table) | real, not fixed | said in GRADING.md; each sample records `entry_is_reference` and the resolve table shows success apart for the reference entry and for other accepted entries |
| Held-back split is public, and compares structures, not exposure | real | reworded in TASK_FORMAT.md and the paper; reported as a description, not a test. Three held-back structures share a protein with a public one: said, not changed |
| F1 floor; weak keyword baseline; grounding pack states the answer; power of small contrasts; track totals not like for like; paraphrases by one author | real, reporting | said in the paper (setup and limitations); clinical results split by whether the literal number is right, follow-ups by edit / no change. A second scripted baseline and an F1 over changed facts only were not built |
| `tr-ligands-8ce0` ("the small molecule" is glycerol), `tr-ions-2p4e` (mercury from a derivative) | real, left | references are right; the wording follows the additive ruling. `tr-nucleic-1bna` no longer says "no ions" |
| Small parsing and labelling edges (representation enum, `" red "`, UniProt keys on a file without SIFTS columns) | real | fixed in `schema.py`, `drawn.py`, `pdbe_state.py` |

## Provider pilot of 2026-11-16 and what it changed (PILOT.md)

The lead ran `run/pilot.toml` for real (39 tasks, one answer each; claude-haiku-4-5 on the
direct route, one free OpenRouter model). All 109 answers were read against request,
reference and grade; `PILOT.md` has the table. Of the 71 answers that are not right, 61 are
the model's fault, 4 the benchmark's, 6 arguable. Three answers had been graded right and
were wrong. No reference answer and no request was wrong. Each fix is in a grader, a
generator or a reference text shown to the models; `tests/test_pilot_fixes.py` and four new
control kinds pin them.

| finding | what was done |
|---|---|
| MVS: a second drawing of the same type on the same atoms is not seen (0 of 7,176 pixels in Mol\* 5.9.0) | the grader keeps the first listed; the MVS reference says so; each sample records `hidden_overlay`; control kinds `overlay_hidden_under_the_same_type`, `overlay_listed_before_the_base` |
| An AlphaFold DB model has one address; an answer on an address that is a 404 had passed | such an address loads nothing, on both tracks; the MVS reference gives the address; `api-016` and two `api-alphafold` tasks no longer accept a v4 file; control kind `alphafold_file_not_served` |
| API: a PDB id in upper case loads nothing in pdbe-molstar 3.3.2 (two answers had passed) | graded as no entry; the API reference says "lower case"; control kind `upper_case_entry_id` |
| API reference did not say that a hide toggle leaves an added representation on screen (nine twins need it) | one sentence in the API reference |
| MVS: a stray key beside `root` was graded as an empty scene | the grader reads the root, as Mol\* does |
| Grounding packs of AlphaFold models said "None" for title and method | 36 packs regenerated |
| Accept-set API tasks did not leave unrequested hide toggles open | `free_hide` by the common rule (14 of 15 tasks) |
| Target score: a backdrop in the right representation counted as half an attempt; alternatives were not tried | half credit only for a drawing confined to the target; best over the accepted alternatives |

56 task files were regenerated: 36 changed in `grounding` only, 14 in `free_hide`, 5 in
`provenance` only, 1 in `accepted`. No `prompt` and no reference changed. A second scripted
baseline (the literal parser) joined the panel on both tracks.

## Checks run on this state (2026-11-23, after the pilot fixes)

| check | result |
|---|---|
| every generator with `--check` (eight), translator `--all --check`, paraphrases `--check`, `build_grounding_packs.py --check`, `build_panel.py --check`, `run/select_pilot.py --check` | all up to date; 79 panel entries checked, 0 bad |
| `scripts/validate_tasks.py --final` | OK: every check passed (879 tasks, 0 old-format) |
| `scripts/check_api_refs.py --cif` (offline, every API task file) | all checks passed |
| `check_api_refs.py --viewer --no-probes --only` the 38 API tasks whose file changed | 158 call lists (references and accepted forms) run in pdbe-molstar 3.3.2, 230 selections compared atom for atom, all agree; `alphafold_view` not run in the viewer in 5 lists |
| `check_api_refs.py --viewer --sample 60 --seed 20261123 --no-probes` | 145 call lists run, 365 selections compared atom for atom, all agree; four annotation settings and one all-models preset not read back |
| `scripts/grader_controls.py --check` | up to date; MVS 1,155 controls on 78 entries, API 1,020 on 74: 0 false passes, 0 false fails |
| `scripts/grader_controls.py --viewer` (Mol\* 5.9.0) | 910 controls, the viewer's verdict agrees on all; 1,545 scenes, the grader's resolved state (drawings as created) equals the viewer's on all; 245 controls of kinds that cannot be read back skipped; rule probes on 78 entries, 3,926 drawings, all agree |
| `scripts/grader_controls.py --viewer-api 150` (pdbe-molstar 3.3.2) | 267 call lists, all agree; a bare load of 73 panel entries, all agree; 3 lists not runnable in the harness, 3 skipped because the grader's rule is that the host serves no file (upper-case id), which the harness cannot show |
| `python -m molbench.runner --manifest run/final_run.toml --dry-run` (all 23 panel entries, mock model) | 91,647 cells, 23 of 23 checks, DRY RUN PASSED; core panel 71,982 calls, projected $137.96 against a cap of $165.00 (lean, one sample: 32,784 calls, $63.43; with the five optional models: 91,647 calls, about $496) |
| `python -m molbench.runner --manifest run/pilot.toml --dry-run` | DRY RUN PASSED, projected $0.24 against a cap of $2.25 |
| `--grade-only` on the pilot archives, both models | 38 of 109 answers right, as in `PILOT.md`; no model called |
| `scripts/paper_tables.py --from-dry-run`, `--from-run results/pilot-v1`, `paper/build.py --check` | 38 mock tables, 3,181 values; the pilot's table in `paper/generated/pilot_results.md`; paper and SI build, nothing stale |
| `uv run pytest -q` | 2,787 passed |

Not re-run in this pass: Mol\* read-backs of MVS references (none changed) and the viewer
read-backs of the follow-up, accept-set and translation generators (`--check --viewer`).
The API viewer check ran on the changed files and a seeded sample of 60, not on all.

**After the merge of the rating tooling and the reviewed paper (same day).** No task file,
prompt or grader rule changed in the merge, and the corpus hash is the same
(`45a841ae…edd8`). Re-run on the merged state, with the same results as in the table: every
generator `--check`, `validate_tasks.py --final`, `check_api_refs.py --cif`,
`grader_controls.py --check`, both dry runs (final manifest: 91,647 cells, 23 of 23 checks,
core panel $137.96 against the cap of $165.00), `paper_tables.py --from-dry-run` (38 mock
tables, 3,181 values), `paper/corpus_values.py --check`, `paper/figures.py --check`,
`paper/build.py --check` and `--pdf`. `uv run pytest -q`: 2,812 passed, none skipped. The
viewer checks and the pilot's `--grade-only` were not run again.

## Known weaknesses

- **Unstated attributes on the API track are mostly an enumerated list.** The accepted
  forms cover what the call format gives naturally (style or default view, backdrop by
  `non_selected_color` or by naming the chains by author or label id, the stretch under an
  added representation in the backdrop, highlight or untouched colour). Hide toggles nobody
  asked for are a grader rule (`free_hide`) only where the task accepts both the cartoon
  style and the default view. An answer that paints an unmentioned component in some other
  colour is still graded as wrong. A form is not offered where the viewer's own default
  drawing of the requested atoms would stay visible in another type (sugars keep their
  3D-SNFG symbols), or where the request is "only chain A" or "nothing else".
- **Twins are not graded by the same leniency.** An MVS answer that draws something the
  request does not name loses success (decision 18); the API twin accepts the default
  view, which draws water and other ligands. The paired analysis is therefore made on the
  target score first; task success is shown beside it, with a sensitivity check without
  the twins that need an unstated hide toggle.
- **Resolve tier: answers on an accepted entry other than the reference entry are graded
  as written** (GRADING.md). A correct selection by chain id fails there. Reported apart.
- **The held-back split is not secret** and compares structures no earlier task used with
  structures earlier tasks used; three held-back structures (5NI1, 2PTC, 3KCG) share a
  protein with a public one.
- **Tier sizes are above the plan** in places, by ruling: translation 73 MVS, grounded 63,
  accept-set 26 + 15, clinical 82.
- **Held-back share is uneven**: 8 of the 31 clinical structures and 4 of the 15 API
  accept-set tasks, against about a fifth elsewhere.
- **Offset pairs rest on four proteins** (HBB five pairs; LYZ, CRYGD, CALM1 one each), and
  their no-offset side is always an AlphaFold model, so "no offset" and "predicted model,
  named by a file URL on the API track" are confounded. The two TP53 pairs (1TUP and the
  AlphaFold model) have no offset on either side. TTR could not get a pair without
  exceeding six tasks on 8C86.
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
