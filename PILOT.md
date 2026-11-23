# The provider pilot of 2026-11-16: what every answer showed

The lead ran `run/pilot.toml` for real on 2026-11-16: 39 tasks picked by rule
(`run/select_pilot.py`: every tier, both tracks, both splits, twins, a follow-up with
no change, the four paraphrases of one request), one answer per task.

* **claude-haiku-4-5**, direct Anthropic route: 46 calls (39 with the format reference,
  7 more with the grounding pack), US $0.21.
* **nvidia/nemotron-3.5-lightning:free**, OpenRouter, $0: 63 calls (39 + 7, and 17 in
  JSON mode). Not a panel model; it proves the route. The first free model tried,
  `google/gemma-4-31b-it:free`, was rate-limited upstream on every call.

Every answer was then read against its request, its reference and its grade: all
non-successes for a verdict, all successes for false passes. This file is the record.
Archives (not in git): `runs/pilot-v1/` (raw calls), `results/pilot-v1/` (grades;
`samples/<condition>/<model>.jsonl` holds one line per answer). The scores below are the
archived answers graded again on 2026-11-23, after the fixes
(`python -m molbench.runner --manifest run/pilot.toml --grade-only`, and the same with
`--free-model nvidia/nemotron-3.5-lightning:free`). No model was called again.

**A pilot, not a result.** 39 hand-ruled tasks and one answer each say that the path
works and where the benchmark was wrong. They say nothing about how good a model is.

## In short

| | answers | right as run | right after the fixes | not right |
|:---|---:|---:|---:|---:|
| claude-haiku-4-5, format reference | 39 | 20 | 20 | 19 |
| claude-haiku-4-5, + grounding pack | 7 | 7 | 6 | 1 |
| nemotron (free), format reference | 39 | 7 | 5 | 34 |
| nemotron (free), + JSON mode | 17 | 6 | 6 | 11 |
| nemotron (free), + grounding pack | 7 | 1 | 1 | 6 |
| **all** | **109** | **41** | **38** | **71** |

The 71 answers that are not right, by verdict:

| Verdict | haiku | nemotron | Meaning |
|:---|---:|---:|:---|
| **a** model at fault | 15 | 46 | the answer is wrong and the request, the reference shown and the grade are sound |
| **b** benchmark at fault | 2 | 2 | a false pass, or a reference shown to the model that left out what the task needs; fixed at the source |
| **c** arguable | 3 | 3 | defensible either way; checked in the real viewer, then ruled |

Of nemotron's 46, 10 are answers the model never got to give: every output token went
into hidden reasoning (footnote 1).

Three answers that had been graded right were wrong (all three are in the table):

1. An AlphaFold model downloaded from an address that does not exist (haiku, with the
   grounding pack). Fixed on 2026-11-22.
2. and 3. A PDB id in upper case on the call-list track (nemotron, twice). The viewer
   loads nothing. Found and fixed on 2026-11-23.

No answer that was graded wrong turned out to be right. No reference was wrong.

## What the pilot found wrong with the benchmark, and what was done

Each was fixed where it comes from (grader, generator, or the reference text shown to
the models), tasks were regenerated, and a pinned test or a control kind keeps it fixed
(`tests/test_pilot_fixes.py`, `tests/controls/`).

| # | Finding | Evidence | Fix |
|---|:---|:---|:---|
| 1 | **A second drawing of the same type on the same atoms is not seen.** "Grey cartoon, residues 84-95 green" answered as a grey cartoon of the polymer plus a green cartoon of the stretch gives a picture that is grey all over. Both pilot models wrote exactly this. A read-back of the viewer's objects lists the green cartoon; the screen does not show it. | Pixels counted in headless Mol\* 5.9.0 for every representation type: 0 of 7,176 green pixels for the cartoon when the grey one is listed first, 4,977 when the green one is listed first (`scripts/check_overlap.py`, `tests/controls/overlap_evidence.json`). | Grader: the first listed of two coincident drawings is the one seen; a larger size factor shows through; surfaces are exempt (`mvs.DrawnStructure.settle`). MVS reference: two lines that say so. Each MVS sample records `hidden_overlay`. Controls: `overlay_hidden_under_the_same_type` (must fail), `overlay_listed_before_the_base` (must pass). |
| 2 | **An AlphaFold DB model has one address.** An answer on `files.rcsb.org/download/AF-P68871-F1.cif` had passed; that address is a 404 and the canvas is empty. The MVS reference did not give the address (the API reference did). | Addresses requested on 2026-11-16: RCSB's host, no model version, v4, lower case all 404; `...-model_v6.cif` 200. | Grader, both tracks: such an address loads nothing (`drawn.alphafold_problem`; MVS outcome `load_failed`). MVS reference gives the address. `api-016` and two `api-alphafold` tasks no longer accept a v4 file. Control `alphafold_file_not_served` on both tracks. |
| 3 | **A PDB id in upper case loads nothing on the call-list track.** Requests write ids in upper case ("Show 3K34"); the free model copied that into `molecule_id`. pdbe-molstar puts the id into PDBe's file address as written, and PDBe has lower-case file names only. Two such answers had passed, and a control kind expected them to. | Run in headless pdbe-molstar 3.3.2 against PDBe on 2026-11-23: `"3K34"` and `"1LMB"` give 0 structures (`3K34.bcif`: 404), `"3k34"` gives 2,387 atoms. RCSB's download host serves either case, so scene-track URLs are not affected. | Grader: an upper-case PDB id is no entry (`pdbe_state.canonical_entry`); a PDBe entry-file URL in upper case likewise, on both tracks (`drawn.pdbe_file_problem`). API reference: `molecule_id` is a PDB id "in lower case"; `"1CBS"` loads nothing. Control `upper_case_entry_id` (must fail, 20); the old kind `entry_id_case_or_url` is now `entry_by_url`. No reference in the corpus was affected. |
| 4 | **The API reference did not say what nine twin tasks need.** "Chain B on its own" is done by hiding the polymer and adding a cartoon for the chain; nothing said that a hide toggle leaves an added representation on screen. | Reference of `tr-chain-only-8c86-api` run in the viewer: agrees. | API reference: one sentence on the hide toggles. |
| 5 | `{"root": {...}, "kind": "root"}` (a stray key beside the root) was graded as an empty scene. Mol\* reads the root. | Rendered in Mol\* both ways: the same picture. | Grader reads the root (`mvs.extract_root`). |
| 6 | Grounding packs of AlphaFold models said "None" for title and method. | The pack text. | `build_grounding_packs.py`: "AlphaFold DB model ..., predicted model, not an experiment". 36 packs regenerated. |
| 7 | Accept-set tasks on the call-list track did not leave the unrequested hide toggles open, as every other API task does. No pilot answer hinged on it. | Reading the task files. | `generate_accept_set_tasks.py`: `free_hide` by the common rule (14 of 15 tasks). |
| 8 | Target score: a backdrop drawn in the right representation counted as half an attempt at the target; and the target score was taken against the reference only, not its accepted alternatives. | Reading the grades of the answers above. | Half credit only for a drawing confined to the target; best over the alternatives. |

## What the lead asked to have explained

**"haiku scored 1.000 on every grounded-condition task but far lower without the
pack."** The pack states the answer. For a clinical task it ends with the mapping
itself, for example `G59D: UniProt position 60 (Gly in UniProt) -> in 1HHO: auth A 59
GLY (label A 59)`; for a resolve task it lists entries of the protein. On the same seven
tasks haiku was right on 5 without the pack and 6 with it. The two it gained are the
two where a numbering offset has to be worked out (`clin-short-target-ins-6tc2-v42a`,
`clin-legacy-context-hba1-1hho-g60d`). The one it lost with the pack is the false pass
of finding 2 (it was 7 of 7 as run). The paper calls this condition an upper bound in
`paper/sections/06_setup.md` ("the lookup already done and its result handed over"),
and so do the caption of the clinical table and the pilot table.

**"The API twins of clinical tasks failed where the MVS twin passed"**
(`clin-legacy-target-hbb-af-p68871-f1-e7v`: scene 1.0, call list 0.5 / 0.0 / 0.0 over
the three wordings). The model, three times, in two ways:

* Full wording: the right residue (UniProt 7), but `color: "purple"` with
  `representation: "spacefill"` and no `representationColor`. The cartoon turns purple
  and the spheres keep their element colours. The API reference states this, and its
  worked example shows the right form. With `representationColor` added, the same
  answer is graded right.
* Indirect and terse wording: `uniprot_residue_number: 6`. E6V is in mature numbering
  and UniProt position 7 was wanted. The same model wrote 7 in all three scene-track
  answers to the same request. One answer per task cannot say whether that is the
  format or chance; the final run's three samples and paired test can.

The prompt, the reference and the grader are sound here: the reference and both
accepted forms run in the viewer and agree.

**`fu-noop-shown-1f88-api`, 0.398.** Arguable, left as designed. The protein already is
a cartoon, so the right answer changes nothing. Both models added
`set_visual_style("cartoon")`, which removes the retinal the user had just coloured red,
the sugars and the waters (stated in the API reference; the grade agrees with the
viewer). "No change" tasks are a deliberate trap (FINAL_PLAN, ruling 19).

**`tr-chain-only-8c86-api`, 0.10.** Both. The reference text was at fault (finding 4).
The answer is also wrong by rules the reference did state: `set_visual_style` comes
last and reloads the structure, which drops the colouring, and nothing hides the other
chains. The picture is the whole entry as a cartoon in default colours.

**"The accept-set tasks all failing."** Four different reasons, none of them the accept
sets. `2cpp` on both tracks: the second ligand selected by a code the entry does not
have (`CCC`, `LIG`; it is `CAM`). `1igt` scene: finding 1 (the selection was right;
listed first it passes). `1igt` call list: `auth_seq_id: 101` together with
`label_comp_id: "ASP"`; in this viewer the component code overrides the number, so every
aspartate turns yellow. The reference states that rule, and both models walked into it.

**`clin-chain-f9-8eph-g412e-chainb-api` and `clin-legacy-target-sod1-2c9v-a5v-api` at
0.** The model, and exactly what the tier is there to measure. F9: the UniProt number
412 written as the author number (the residue is label 186 of chain B). SOD1: UniProt
position 5 worked out correctly, then written as the author number; 2C9V is numbered as
the mature protein, so author 5 is the neighbour. In both, `uniprot_residue_number`
(the reference form) would have been right.

## Every answer that is not right

Scores are after the fixes. *F1 / target*: strict F1 of the whole final state, and the
target score (the requested atoms drawn as asked; "–" where a task has none).
*Condition*: "reference" is the headline condition (format reference only).

| Model | Condition | Task | F1 / target | Outcome | Verdict | What happened | Action |
|:---|:---|:---|:---|:---|:---|:---|:---|
| haiku | reference | `acc-ligand-colours-2cpp-api` | 0.79 / 0.50 | valid | **a** | second ligand selected as `LIG`, a code 2CPP does not have (it is `CAM`); haem right | none |
| haiku | reference | `acc-ligand-colours-2cpp-mvs` | 0.80 / 0.50 | valid | **a** | second ligand selected as `CCC`, a code 2CPP does not have (`CAM`); haem right | none |
| haiku | reference | `acc-residue-colour-1igt-api` | 0.68 / 0.06 | valid | **a** | `auth_seq_id: 101` with `label_comp_id: "ASP"`: the component code overrides the number (stated in the API reference, checked in the viewer), so every Asp turns yellow | none |
| haiku | reference | `acc-residue-colour-1igt-mvs` | 0.86 / 0.00 | valid | **c** | Mol\* shows the second of two same-type drawings on the same atoms not at all (0 green pixels of 7,176): the picture is grey all over. The selection itself is right (listed first, the answer passes) | grader follows the viewer (`DrawnStructure.settle`), MVS reference now says so, control kinds `overlay_*` |
| haiku | reference | `clin-chain-f9-8eph-g412e-chainb-api` | 0.00 / 0.00 | valid | **a** | used the UniProt number 412 as the author number (the residue is label 186 in chain B); the reference form `uniprot_residue_number` was open to it | none |
| haiku | reference | `clin-legacy-context-hba1-1hho-g60d-mvs` | 0.75 / 0.00 | valid | **a** | G59D is already in mature numbering and 1HHO is numbered that way (author 59); the answer added one and drew 60 | none |
| haiku | reference | `clin-legacy-target-hbb-af-p68871-f1-e7v-api` | 0.50 / 0.75 | valid | **a** | right residue (UniProt 7), but `color: purple` with `representation: spacefill` and no `representationColor`: the cartoon turns purple and the added spheres stay element-coloured (stated in the API reference; with `representationColor` added the answer passes) | none |
| haiku | reference | `clin-legacy-target-hbb-af-p68871-f1-e7v-api.indirect` | 0.00 / 0.00 | valid | **a** | `uniprot_residue_number: 6`: the mature-numbering offset not applied (its scene-track answers to the same request all drew 7); also no `representationColor` and an unrequested pLDDT colouring | none |
| haiku | reference | `clin-legacy-target-hbb-af-p68871-f1-e7v-api.terse` | 0.00 / 0.00 | valid | **a** | `uniprot_residue_number: 6` again, and the whole model switched to spacefill | none |
| haiku | reference | `clin-legacy-target-sod1-2c9v-a5v-api` | 0.00 / 0.00 | valid | **a** | worked out UniProt position 5 correctly, then wrote it as the author number: 2C9V is numbered as the mature protein, so author 5 is the next residue | none |
| haiku | reference | `clin-short-target-ins-6tc2-v42a-mvs` | 0.00 / 0.00 | valid | **a** | p.V42 drawn as author 42 in chains A and B; it is author 18 in the six B chains (B, D, F, H, J, L) | none |
| haiku | reference | `fu-noop-shown-1f88-api` | 0.40 / – | valid | **c** | "Cartoon for the protein, please" when the protein already is a cartoon: the answer adds `set_visual_style("cartoon")`, which removes the retinal the user had just coloured, the sugars and the waters. The task is a deliberate "no change needed" trap (FINAL_PLAN ruling 19); the reference stated the side effect of the cartoon style already | left as designed |
| haiku | reference | `gr-attachment-1hrc-hec` | 0.67 / 0.00 | valid | **a** | haem selected as `HEM` (it is `HEC` in 1HRC) and Cys20/Cys102 drawn; the attached cysteines are 14 and 17 | none |
| haiku | reference | `gr-attachment-1hrc-hec-api` | 0.53 / 0.00 | valid | **a** | `HEM` again, Cys20 and 23 | none |
| haiku | reference | `gr-disulfides-3kcg` | 0.86 / 0.00 | valid | **a** | six residues of a chain A that 3KCG does not have; the 20 disulfide cysteines are in chains L, H and I | none |
| haiku | reference | `gr-glyco-sites-9fb2-api` | 0.66 / 0.00 | valid | **a** | Asn301 and 334 drawn; the glycosylated ones are 58, 98 and 309 | none |
| haiku | reference | `gr-metal-site-2c9v-zn-api` | 0.33 / 0.00 | valid | **a** | wrong residues (54, 57, 61, 110 of chain A only; the sites are 63, 71, 80, 83 of A and F), `color` where `representationColor` was needed | none |
| haiku | reference | `tr-chain-only-8c86-api` | 0.10 / 0.00 | valid | **b** | the task needs "hide the polymer, then add a cartoon for the chain", and the API reference did not say that a hide toggle leaves an added representation on screen. The answer is wrong on its own account as well: `set_visual_style` comes last and reloads the structure, which drops the colouring (stated in the reference), and nothing hides the other chains | API reference now states it (nine twins need it); reference checked in the viewer |
| haiku | reference | `tr-range-rows-3k34` | 0.79 / 0.00 | valid | **c** | Mol\* shows the second of two same-type drawings on the same atoms not at all (0 green pixels of 7,176): the picture is grey all over. The selection itself is right (listed first, the answer passes) | grader follows the viewer (`DrawnStructure.settle`), MVS reference now says so, control kinds `overlay_*` |
| haiku | + grounded | `clin-legacy-target-hbb-af-p68871-f1-e7v-mvs.terse` | 0.00 / 0.00 | load_failed | **b** | downloads `files.rcsb.org/download/AF-P68871-F1.cif`, which does not exist (404): empty canvas. **Was graded right** (any URL naming the model counted). The MVS reference did not give the AlphaFold DB address; the API reference did | grader: `alphafold_problem`, outcome `load_failed`; MVS reference gives the address; control kind `alphafold_file_not_served` |
| nemotron | reference | `acc-ligand-colours-2cpp-api` | 0.00 / 0.00 | invalid_json | **a**¹ | no answer: all 8,000 output tokens went into hidden reasoning (finish reason `length`) | the free route is started with `--free-model-reasoning` (16,000 tokens) for such a model |
| nemotron | reference | `acc-ligand-colours-2cpp-mvs` | 0.00 / 0.00 | invalid_json | **a**¹ | cut off at the token limit in the middle of the scene (7,866 of 8,000 tokens were hidden reasoning) | as above |
| nemotron | reference | `acc-residue-colour-1igt-api` | 0.68 / 0.06 | valid | **a** | as haiku: `label_comp_id: "ASP"` overrides the residue number, every Asp yellow | none |
| nemotron | reference | `acc-residue-colour-1igt-mvs` | 0.00 / 0.00 | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be valid with F1 0.857) | none (strict score 0; the repaired score is reported apart) |
| nemotron | reference | `api-label-chain-1lmb` | 0.00 / 0.00 | valid | **b** | `molecule_id` in upper case, as the request writes it. pdbe-molstar asks PDBe for `{id}.bcif` as written, PDBe answers 404, nothing loads (run in the viewer 2026-11-23). **Was graded right** | grader: an upper-case id loads nothing; API reference says "lower case"; control kind `upper_case_entry_id`; the control that expected a pass corrected |
| nemotron | reference | `api-undo-8k7f` | 0.00 / 0.00 | valid | **a** | the same trap in the tooltips: `label_comp_id: "TYR"` beside the number puts the tooltip on every Tyr of chain B (and the id is upper case: loads nothing) | none |
| nemotron | reference | `clin-chain-f9-8eph-g412e-chainb-api` | 0.00 / 0.00 | valid | **a** | UniProt number 412 as the author number, as haiku | none |
| nemotron | reference | `clin-legacy-context-hba1-1hho-g60d-mvs` | 0.00 / 0.00 | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be valid with F1 0.75) | none (strict score 0; the repaired score is reported apart) |
| nemotron | reference | `clin-legacy-target-hbb-af-p68871-f1-e7v-api` | 0.00 / 0.00 | invalid_json | **a**¹ | no answer: all 8,000 output tokens went into hidden reasoning (finish reason `length`) | the free route is started with `--free-model-reasoning` (16,000 tokens) for such a model |
| nemotron | reference | `clin-legacy-target-hbb-af-p68871-f1-e7v-api.indirect` | 0.00 / 0.00 | valid | **a** | author residue 6: offset not applied | none |
| nemotron | reference | `clin-legacy-target-hbb-af-p68871-f1-e7v-api.terse` | 0.00 / 0.00 | valid | **a** | author residue 6, and `color` where `representationColor` was needed | none |
| nemotron | reference | `clin-legacy-target-hbb-af-p68871-f1-e7v-mvs` | 0.00 / 0.00 | invalid_json | **a**¹ | no answer: all 8,000 output tokens went into hidden reasoning (finish reason `length`) | the free route is started with `--free-model-reasoning` (16,000 tokens) for such a model |
| nemotron | reference | `clin-legacy-target-hbb-af-p68871-f1-e7v-mvs.indirect` | 0.00 / 0.00 | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be load_failed with F1 0.0) | none (strict score 0; the repaired score is reported apart) |
| nemotron | reference | `clin-legacy-target-hbb-af-p68871-f1-e7v-mvs.terse` | 0.00 / 0.00 | invalid_json | **a**¹ | no answer: all 8,000 output tokens went into hidden reasoning (finish reason `length`) | the free route is started with `--free-model-reasoning` (16,000 tokens) for such a model |
| nemotron | reference | `clin-legacy-target-sod1-2c9v-a5v-api` | 0.40 / 0.67 | valid | **a** | right residue in chain A; the second copy addressed as chain B (it is author chain F), and everything else painted white unasked | none |
| nemotron | reference | `clin-short-target-ins-6tc2-v42a-mvs` | 0.00 / 0.00 | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be valid with F1 0.0) | none (strict score 0; the repaired score is reported apart) |
| nemotron | reference | `fu-noop-hidden-8k7f-mvs` | 0.00 / – | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be invalid_mvs with F1 0.0) | none (strict score 0; the repaired score is reported apart) |
| nemotron | reference | `fu-noop-shown-1f88-api` | 0.00 / – | valid | **c** | as haiku, and `set_visual_style` placed after the colouring, which the reload then drops | left as designed |
| nemotron | reference | `fu-noop-spin-1cbs-mvs` | 0.00 / – | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be invalid_mvs with F1 0.0) | none (strict score 0; the repaired score is reported apart) |
| nemotron | reference | `fu-referent-colour-5cj6-mvs` | 0.00 / 0.00 | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be invalid_mvs with F1 0.0) | none (strict score 0; the repaired score is reported apart) |
| nemotron | reference | `gr-attachment-1hrc-hec` | 0.80 / 0.50 | valid | **a** | cysteines 14 and 17 right; haem selected as `HEM` (it is `HEC`), so no haem is drawn | none |
| nemotron | reference | `gr-attachment-1hrc-hec-api` | 0.00 / 0.00 | valid | **a** | `HEM`, Cys77 and 102, id in upper case | none |
| nemotron | reference | `gr-disulfides-3kcg` | 0.00 / 0.00 | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be valid with F1 1.0) | none (strict score 0; the repaired score is reported apart) |
| nemotron | reference | `gr-glyco-sites-9fb2-api` | 0.00 / 0.00 | valid | **a** | every asparagine drawn, not the three glycosylated ones; id in upper case | none |
| nemotron | reference | `gr-ligand-1ake-ap5` | 0.00 / 0.00 | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be valid with F1 0.6667) | none (strict score 0; the repaired score is reported apart) |
| nemotron | reference | `gr-metal-site-2c9v-zn-api` | 0.00 / 0.00 | invalid_json | **a**¹ | no answer: all 8,000 output tokens went into hidden reasoning (finish reason `length`) | the free route is started with `--free-model-reasoning` (16,000 tokens) for such a model |
| nemotron | reference | `in-ca-distance-1ake` | 0.00 / 0.00 | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be valid with F1 1.0) | none (strict score 0; the repaired score is reported apart) |
| nemotron | reference | `in-transparent-1rx2-nap` | 0.00 / 0.00 | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be valid with F1 0.6667) | none (strict score 0; the repaired score is reported apart) |
| nemotron | reference | `res-complex-p69905-p68871` | 0.00 / 0.00 | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be valid with F1 0.0) | none (strict score 0; the repaired score is reported apart) |
| nemotron | reference | `res-name-p02649` | 0.00 / 0.00 | valid | **a** | 1LP9 is not apolipoprotein E | none |
| nemotron | reference | `tr-chain-only-8c86-api` | 0.00 / 0.00 | invalid_json | **a**¹ | no answer: all 8,000 output tokens went into hidden reasoning (finish reason `length`) | the free route is started with `--free-model-reasoning` (16,000 tokens) for such a model |
| nemotron | reference | `tr-range-rows-3k34` | 0.00 / 0.00 | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be invalid_mvs with F1 0.0) | none (strict score 0; the repaired score is reported apart) |
| nemotron | reference | `tr-range-rows-3k34-api` | 0.00 / 0.00 | valid | **b** | `molecule_id` in upper case, as the request writes it. pdbe-molstar asks PDBe for `{id}.bcif` as written, PDBe answers 404, nothing loads (run in the viewer 2026-11-23). **Was graded right** | grader: an upper-case id loads nothing; API reference says "lower case"; control kind `upper_case_entry_id`; the control that expected a pass corrected |
| nemotron | reference | `tr-rep-word-1mbn` | 0.00 / 0.00 | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be valid with F1 1.0) | none (strict score 0; the repaired score is reported apart) |
| nemotron | + grounded | `clin-legacy-context-hba1-1hho-g60d-mvs` | 0.00 / 0.00 | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be invalid_mvs with F1 0.0) | none (strict score 0; the repaired score is reported apart) |
| nemotron | + grounded | `clin-legacy-target-hbb-af-p68871-f1-e7v-mvs` | 0.00 / 0.00 | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be load_failed with F1 0.0) | none (strict score 0; the repaired score is reported apart) |
| nemotron | + grounded | `clin-legacy-target-hbb-af-p68871-f1-e7v-mvs.indirect` | 0.00 / 0.00 | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be load_failed with F1 0.0) | none (strict score 0; the repaired score is reported apart) |
| nemotron | + grounded | `clin-legacy-target-hbb-af-p68871-f1-e7v-mvs.terse` | 0.00 / 0.00 | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be valid with F1 0.0) | none (strict score 0; the repaired score is reported apart) |
| nemotron | + grounded | `res-complex-p69905-p68871` | 0.00 / 0.00 | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be valid with F1 1.0) | none (strict score 0; the repaired score is reported apart) |
| nemotron | + grounded | `res-name-p02649` | 0.00 / 0.00 | invalid_json | **a** | brackets do not balance at the end of the one-line scene: not JSON, and Mol\* does not load it (repaired it would be valid with F1 1.0) | none (strict score 0; the repaired score is reported apart) |
| nemotron | + structured | `acc-ligand-colours-2cpp-api` | 0.00 / 0.00 | invalid_json | **a**¹ | no answer: all 8,000 output tokens went into hidden reasoning (finish reason `length`) | the free route is started with `--free-model-reasoning` (16,000 tokens) for such a model |
| nemotron | + structured | `acc-ligand-colours-2cpp-mvs` | 0.00 / 0.00 | invalid_mvs | **a** | malformed tree (a bare string among the nodes): Mol\* rejects it | none |
| nemotron | + structured | `acc-residue-colour-1igt-api` | 0.68 / 0.06 | valid | **a** | the same answer again | none |
| nemotron | + structured | `acc-residue-colour-1igt-mvs` | 0.86 / 0.00 | valid | **a** | Asp101 looked for in chain A, where residue 101 is not Asp (it is in B and D): nothing is selected | none |
| nemotron | + structured | `fu-noop-hidden-8k7f-mvs` | 0.00 / – | invalid_json | **a** | JSON mode: a complete scene, then 64,403 characters of white space up to the token limit; not valid JSON as sent (repaired it would score 1.0) | none (reported apart as repaired) |
| nemotron | + structured | `fu-noop-shown-1f88-api` | 0.00 / – | valid | **c** | the same answer again | left as designed |
| nemotron | + structured | `fu-noop-spin-1cbs-mvs` | 0.00 / – | invalid_json | **a** | JSON mode: a complete scene, then 10,802 characters of white space up to the token limit; not valid JSON as sent (repaired it would score 1.0) | none (reported apart as repaired) |
| nemotron | + structured | `tr-chain-only-8c86-api` | 0.00 / 0.00 | invalid_json | **a**¹ | no answer: all 8,000 output tokens went into hidden reasoning (finish reason `length`) | the free route is started with `--free-model-reasoning` (16,000 tokens) for such a model |
| nemotron | + structured | `tr-het-code-6tha` | 0.00 / 0.00 | invalid_mvs | **a** | a component nested inside a component: Mol\* rejects the tree | none |
| nemotron | + structured | `tr-range-rows-3k34` | 0.79 / 0.00 | valid | **c** | same-type cartoons over each other, as haiku: grey all over. Written as `{"root": {...}, "kind": "root"}`, which **was graded as an empty scene**; Mol\* reads the root | grader reads the root as Mol\* does; then the overlap rule applies |
| nemotron | + structured | `tr-range-rows-3k34-api` | 0.00 / 0.00 | invalid_json | **a**¹ | no answer: all 8,000 output tokens went into hidden reasoning (finish reason `length`) | the free route is started with `--free-model-reasoning` (16,000 tokens) for such a model |

¹ Run setting, not only the model: nemotron reasons before it answers and was started
with the 8,000-token limit of a model that does not. A model flagged as reasoning gets
16,000 (`run.reasoning_max_tokens`). The free route now has `--free-model-reasoning`
for this. In the final manifest every reasoning model is flagged.

Successes were read too. Apart from the three false passes above, the 38 are right:
identical to the reference, or differing in ways that give the same picture
(`"protein"` for `"polymer"` on entries with no nucleic acid, `grey` for `gray`, one
`color` call for two, another accepted entry on the resolve tier, upper-case ids on
RCSB's host).

## What the pilot proved about the provider path

**Cost projection (Anthropic route, priced).** Projected on the corpus as run: 157,213
input and 15,033 output tokens, $0.23. Billed: 148,309 input (6% under) and 13,203
output (12% under), $0.2143 (7% under). Longest answer 744 tokens, against a limit of
8,000. The projection errs on the safe side by a few percent. Anthropic returns no cost
field, so the archive records `cost_source: "price"` (tokens times list price).

**OpenRouter route.** Every one of the 63 records has `usage.cost` (0.0, recorded as
`cost_source: "provider"`), the serving `provider` ("Nvidia"), `response_model`,
`response_id`, the finish reason and `reasoning_tokens`. The adapter keeps a missing
cost apart from a cost of zero. No field was missing or mis-read; the adapter needed no
change.

**Token counts and finish reasons.**

| | calls | input tokens | output tokens | of which hidden reasoning | finish reasons | attempts |
|:---|---:|---:|---:|---:|:---|:---|
| haiku | 46 | 148,309 | 13,203 | 0 | `end_turn` 46 | 1 each |
| nemotron | 63 | 182,789 | 258,576 | 236,324 (91%) | `stop` 51, `length` 12 | 1 each |

Nemotron's output was 13 times the projection for a model that does not reason
(19,805), and ten hidden tokens for every visible one. The final manifest plans about
three for its reasoning models. At price zero this cost nothing; on a priced reasoning
model it is the main budget risk, and the hard cap is what bounds it.

**JSON mode (`response_format: json_object`).** Requested on 17 calls and recorded
(`request.structured`). On the call-list track the answer comes back as
`{"actions": [...]}` and the runner unwraps it (5 of 5 non-empty answers). It did not
make the output valid: 2 answers were a complete scene followed by white space up to the
token limit (64,403 and 10,802 characters), 2 were trees Mol\* rejects, 3 were empty
(footnote 1). JSON mode is not wired for the Anthropic route, so haiku has no cells in
that condition, as planned.

**Errors.** `runs/pilot-v1/errors.jsonl` has 45 entries, of two kinds: 27 are the gemma
429s, and 18 are haiku cells of the first start, which failed with `No module named
'anthropic'` (the SDK extra was not installed). Nothing was billed for either. A missing
SDK now stops the run before the first call (`runner.preflight`).

**Resume and re-grading.** The run was started four times on one archive and never
repeated a call. Re-grading an archive on a corpus that has moved works and names the
tasks that changed.

## What it changes

* **Grader**: findings 1, 2, 3, 5, 8. GRADING.md has each rule with its evidence.
  Controls: 1,155 on the scene track, 1,020 on the call-list track, 0 false passes,
  0 false fails.
* **References shown to the models**: two additions to the MVS reference (AlphaFold
  address, coincident drawings), two to the API reference (hide toggles, lower-case
  id). The prompts are a few lines longer; run sizes were projected again
  (`run/README.md`).
* **Corpus**: 56 task files regenerated (grounding packs, `free_hide`, AlphaFold
  versions). No request and no reference answer changed; the accepted alternative of
  `api-016` was corrected.
* **Runner**: any free model by flag; SDK checked before the first call; a pilot can be
  graded again on a corpus that moved; `hidden_overlay` per sample; per-sample cost in
  the scorecard.
* **Not changed**, and why: "no change" follow-ups (designed); the component-code rule
  of the API (real viewer behaviour, stated in the reference); strict scoring of
  unbalanced JSON (Mol\* does not load it; the repaired score is reported apart).

## For the lead to rule on

* **Upper-case ids (finding 3).** The grade now follows the viewer and the reference
  says so. It is a trivial slip that scores 0 on the whole task, and requests spell ids
  in upper case. The alternative is to accept either case on the grounds that a wrapper
  could lower-case it. The AlphaFold ruling went the viewer's way, so this one did too.
* **Hidden reasoning.** A reasoning model can spend ten tokens thinking for each one it
  writes. The manifest's projection assumes about three for the models flagged
  `reasoning = true`.
