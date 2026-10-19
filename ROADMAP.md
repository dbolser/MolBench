# MolBench — next-phase plan

Status: Component 1 (deterministic scene-spec grading) is implemented across three
grounded task regimes with an 8-model leaderboard. The next phase makes the
benchmark *complete and publishable*: implement Component 2 (visual grading),
sharpen Component 1, and validate the instrument.

---

## Revised plan (2026-10-04) — read this first

Three decisions, each backed by a test this round.

**1. MVS stays the target. The bottleneck was our reference, not MVS.**
The chat driver told a user "MVS cannot show hydrogen bonds". Checked against the
Mol\* 5.9.0 source and real renders, that is wrong: `primitives` draws dashed lines
between named atoms (`distance_measurement`, labelled with the length), and Mol\*
computes H-bonds/metal contacts itself via `custom.molstar_show_non_covalent_interactions`
on a component. Our reference listed only 8 node kinds (one of them wrong), so no
model could ever draw an H-bond. A 4-prompt × 2-model A/B: old reference 0/4
lines drawn and 2 Mol\* crashes on "50% transparent"; new reference 4/4 lines and
2/2 transparency. Models still pick wrong chains/atoms (see grounding below).
What MVS truly cannot do: select by distance or property, compute a
superposition, style the computed interactions. Those stay in the API track.

**2. Prompting conditions: a 2×2, no public "tuned" row.**

| | no grounding | grounding pack |
|---|---|---|
| **bare** (output contract only) | what the model knows | knows facts, not MVS |
| **spec** (vendored MVS reference) | **headline** | upper bound for an offline pipeline |

* *Spec* = `molbench/mvs_reference.md`, a neutral, complete snapshot of MVS as
  Mol\* 5.9.0 implements it. `--condition bare|spec` selects the row (done).
* *Grounding pack* = facts about the task's structure prepared **offline** and
  frozen with the task: chain ids and residue ranges, ligand codes and atom names,
  SIFTS/UniProt mapping, ClinVar positions, the accepted entry ids. Reproducible
  by construction; no live calls during a run. Can be ablated separately
  (MVS-reference vs molecular-grounding).
* The chat driver's own prompt is **tuned** on everything it sees and is owned by
  `molstar-chat-driver`. It is not scored as a model comparison. Product claims
  come from real user prompts that arrive *after* a prompt version is frozen
  (graded by thumbs up/down or the C2 judge). Curated user prompts become new
  benchmark tasks — after which they are dev data for the next prompt version.

**3. External resources (PubMed, PDB, UniProt, ClinVar): closed-book core.**
Lookups enter only as the frozen grounding pack above. Build a live tool loop
only if grounding lifts the lookup-heavy tasks (`mvs_clinical`, `mvs_resolve`)
by ≥10 F1 points on a few cheap models. *(Tested 2026-10-18: not met — see the
2×2 result below.)* PubMed is out of scope. This keeps
MolBench a visualization benchmark that *measures* the value of lookups rather
than an API-calling benchmark.

### Work list

| # | item | status |
|---|---|---|
| R1 | Spec reference v2 (primitives, opacity, interactions, colour themes, fixed rep types) | done |
| R2 | Grader: primitives keyed on shape + atom pair (styling/direction ignored); interactions flag and colour theme graded | done |
| R3 | `tasks/mvs_interactions/` — 6 tasks, every atom checked against the mmCIF with gemmi (`scripts/author_interaction_tasks.py`) | done |
| R4 | `--condition bare\|spec` in the runner, recorded in run meta | done |
| R5 | Regression run: old vs spec vs bare on 3 cheap models, all MVS tasks | done — see below |
| R6 | Grounding packs: offline builder (gemmi + SIFTS + existing resolve/clinical provenance) and `--grounding` flag | done (PR #9) |
| R7 | Grader: resolve selections to atom sets against the mmCIF, so equivalent namings (`label_comp_id`+atom vs residue number+atom) match and empty selections score zero | done (PR #10) |
| R8 | Chat driver v2: new reference in its prompt + empty-selection lint (a primitive end that matches nothing is drawn to the origin by Mol\*) | shipped (chat-driver #18, deployed 2026-10-06) |
| R9 | Chat driver: thumbs up/down per turn, for grading real traffic | todo |
| R10 | Leaderboard: regimes for `resolve` and `interactions` sources (unknown sources now raise) | done |

**R5 result (2026-10-06, 1 sample, 76 tasks, ~$0.85).** Mean F1:

| model | old ref | spec | bare | interaction tasks old → spec |
|---|---|---|---|---|
| Claude Haiku 4.5 | 0.800 | 0.806 | 0.061 | 0.52 → 0.72 |
| DeepSeek V3.2 | 0.827 | 0.814 | 0.018 | 0.58 → 0.56 |
| Qwen3-30B-A3B | 0.576 | 0.522 | 0.000 | 0.22 → 0.18 |

* **Bare ≈ 0 for every model.** MVS is not in pretraining in any usable form;
  the bare row measures nothing but "can't". Keep it as one line in the paper,
  not a leaderboard column.
* **Spec costs ~0.01 on the old tasks for the strong models** (within 1-sample
  noise: 57 tasks better, 63 worse of 228). Part of it is real: with a richer
  reference, Haiku adds unrequested ball-and-stick on the resolve tasks
  (same, correct entries; precision drops).
* **The small model loses ~0.05, almost all to JSON bracket-count errors** on a
  ~2.4× longer prompt (parse success 0.78 → 0.67). Longer documentation hurts
  small models — a finding, and an argument for B6 (structured outputs).
* Interaction tasks are not yet solved by anyone: line endpoints are named with
  the wrong atoms or chains. That is the grounding gap (R6).

**2×2 result (2026-10-18, 1 sample, 70 tasks, R7 grader, Mol*-validated).**
15 models × spec / spec + grounding pack ("dossier"); 3 models × bare / bare +
dossier. A scene Mol* rejects scores 0. Published on the leaderboard
(`scripts/build_site_data.py`).

| model | spec | + dossier | valid scenes | Δ on tasks valid in both (n) | Δ lookup tasks (15) |
|---|---|---|---|---|---|
| deepseek-v3.2 | 0.916 | 0.901 | 99% → 97% | −0.013 (67) | −0.152 |
| claude-haiku-4-5 | 0.870 | 0.855 | 96% → 93% | −0.002 (65) | −0.051 |
| deepseek-v4-flash | 0.861 | 0.778 | 93% → 84% | −0.012 (55) | −0.073 |
| gemini-3.5-flash | 0.845 | 0.812 | 94% → 90% | −0.013 (62) | −0.130 |
| minimax-m3 | 0.830 | 0.827 | 90% → 91% | −0.013 (59) | −0.037 |
| qwen3-next-80b | 0.819 | 0.843 | 91% → 91% | +0.020 (60) | +0.040 |
| glm-5.2 | 0.807 | 0.786 | 90% → 86% | +0.007 (56) | −0.124 |
| llama-4-maverick | 0.794 | 0.789 | 81% → 83% | −0.007 (52) | +0.127 |
| gemma-3-27b | 0.724 | 0.662 | 81% → 70% | +0.028 (47) | −0.159 |
| kimi-k2.6 | 0.663 | 0.573 | 73% → 64% | −0.008 (36) | −0.027 |
| gpt-5.4-nano | 0.658 | 0.613 | 76% → 76% | −0.046 (40) | +0.085 |
| gpt-oss-120b | 0.574 | 0.590 | 63% → 66% | −0.011 (26) | +0.160 |
| qwen3-30b | 0.529 | 0.276 | 56% → 31% | −0.011 (16) | +0.042 |
| gpt-oss-20b | 0.252 | 0.205 | 29% → 24% | +0.033 (6) | +0.012 |
| nemotron-3-super | 0.077 | 0.081 | 9% → 9% | — (0) | −0.035 |

* **Dossiers don't lift scores.** Mean Δ −0.042. On the 647 task × model pairs
  valid in both runs, Δ −0.005 (66 better, 93 worse, 488 the same). The overall
  drop is more invalid output on the longer prompt (qwen3-30b 56% → 31% valid).
* **The tool-loop trigger is not met.** On the 15 lookup-heavy tasks (clinical +
  resolve) the mean Δ is −0.021. Two models pass +0.10 (gpt-oss-120b, llama-4),
  four lose as much; the gains are invalid → valid flips (one flip ≈ 0.05 here),
  not better answers. No live tool loop for now.
* **Bare = 0 for all.** 0 of 420 bare scenes are valid. Most parse as JSON but put
  parameters on the node instead of under `params`; Mol* rejects them. MVS is not
  in pretraining.
* **Failures are mostly invalid JSON.** Spec run: 227 of 266 failed samples are
  invalid JSON (mostly "Expecting ',' delimiter"), 36 invalid MVS (mostly `focus`
  placed under `structure`), 3 failed to load. Valid-scene rate alone tracks MVS
  F1 at r = 0.996 across the 15 models; over valid scenes they cluster at
  0.87–0.98. B6 (structured outputs) is the obvious next lever.
* Gaps: `mistral-small-2603` could not be run (OpenRouter upstream rate limit,
  11 attempts). The qwen3-30b spec run's archive was never written, so its raw
  text is missing on the failures page (outcomes and errors are intact).
  gemini-3.5-flash and gpt-5.4-nano ran via OpenRouter, not the native APIs.

---

## Phase A — Component 2: render + VLM judge  ← the headline

### Status (2026-10-18)

"The VLM" is two separate judges. One is live, one is a sketch.

| piece | state |
|---|---|
| A0 renderer (`render.py`, Playwright + Mol\* 5.9.0) | **done** |
| Image-pair judge (`AnthropicImagePairJudge`, escalation tier T2) | **live** — run on the original 7 models (Jun 2026), then on 15 models with R7 + strict T1 (2026-10-18, spec condition, judge `claude-opus-4-8`) |
| Rubric judge (`AnthropicVLMJudge`, Component 2 proper) | **sketch** — one call, no decompose/extract protocol, never run. The runner uses `StubVLMJudge` |
| A2 runner wiring for `visual_rubric` | not started |
| A3 Component-2 corpus | 2 tasks, written as API actions, not MVS, so `render.py` can't draw their references |
| A4 human-agreement study | rating set + analysis built; rating page on the evaluator site; collecting |

**The escalation result is mostly the pixel diff, not the VLM.** Of 196 rescues
(253 escalated, 7 models), 187 came from T1 visual diff and 9 from the VLM.

**T1 gives false rescues (measured 2026-10-18).** It is a whole-image RMSE at
128 px with a 0.97 threshold. A one-residue highlight is a few pixels, so wrong
scenes pass. On `clinvar-1tup-D281` (red ball-and-stick at A281):

| wrong prediction | tree F1 | visual sim | T1 verdict |
|---|---|---|---|
| residue 175 instead of 281 | 0.889 | 0.994 | rescued |
| residue 282 (neighbour) | 0.889 | 0.992 | rescued |
| blue instead of red | 0.889 | 0.997 | rescued |
| chain B instead of A | 0.889 | 0.994 | rescued |

**Fixed and measured (2026-10-18).** T1 now rescues only near-identical renders
(≤ 2 pixels changing by > 48 in any channel, at 256 px; `visual.changed_pixels`).
A re-render changes 0 pixels; the four wrong scenes above change 8–30. On the
June escalation, 176 of the 187 T1 rescues are pixel-identical and stay rescued;
11 (partial disulfide sets, `mvs-003` wrong residue, `ligand` vs `HEM`) now go to
T2. Re-scoring offline with R7 + strict T1 (stored VLM verdicts reused, the 11
counted as not rescued) moves every model's validated F1 by +0.00 to +0.03, so
the published numbers stand. And R7 tree match alone, with no rendering, lands
within ~0.01 of the published validated F1 for most models: atom-set grading
recovers what the render cascade was rescuing.

| model | published validated | R7 tree only | R7 + strict T1 + stored T2 |
|---|---|---|---|
| claude-haiku-4-5 | 0.945 | 0.948 | 0.955 |
| deepseek-v3.2 | 0.939 | 0.945 | 0.949 |
| gemini-3.5-flash | 0.907 | 0.897 | 0.909 |
| gemma-3-27b-it | 0.903 | 0.898 | 0.903 |
| gpt-5.4-nano | 0.781 | 0.776 | 0.786 |
| qwen3-30b-a3b | 0.704 | 0.727 | 0.735 |
| gpt-oss-20b | 0.461 | 0.455 | 0.458 |

**Re-run 2026-10-18 on 15 models** (spec condition, R7, strict T1, Mol*-validated).
Of 285 valid but imperfect scenes, 127 were rescued: 48 pixel-identical at T1,
79 judged "same" by the VLM; 158 judged different. With strict T1 the VLM now
does most of the rescuing, so its verdicts need the human check (A4) before
validated F1 is more than a side column. Validated − tree F1 is +0.00 to +0.03
per model. Now on the leaderboard, with a gallery of 12 cards picked by a fixed
rule.

Open-ended requests ("show the key hydrogen bond", "highlight the allosteric
change") cannot be graded by tree-matching: many distinct scenes satisfy them.
Component 2 renders the model's scene and scores the *image* against a rubric.

### A0. Decision: how do we render an MVS scene to a PNG? (do this first)
The crux of the whole phase. Options, with trade-offs:

| Approach | Pros | Cons |
|---|---|---|
| **Playwright + minimal Mol\* HTML** (recommended v1) | Python-native (already in `execute` extra); no Node toolchain; uses the same Mol\* the benchmark targets | heavier (Chromium), canvas-timing flakiness to manage |
| Headless Mol\* (Node + `gl`) | no browser, fast, scriptable | Node toolchain; more setup; another language in the repo |
| Hosted MVS→image service | trivial client | external dependency; reproducibility/availability risk |

**Recommendation:** Playwright v1. Build `molbench/render.py` exposing
`render_scene(scene_tree, out_png, width, height) -> Path`: write the MVS state to
a temp file, load a fixed local HTML page that embeds Mol\* + the MVS extension,
wait for a render-complete signal, screenshot the canvas. Pin the Mol\* version.
**Exit criterion:** a reference scene (e.g. `mvs-002` heme) renders to a
recognisable PNG deterministically across 3 runs.

### A1. VLM judge (`molbench/vlm_grader.py`, flesh out `AnthropicVLMJudge`)
Implement the **decompose → extract → compare → score** protocol (avoids naive
"is this correct?" bias):
1. **Decompose** the prompt into discrete visual constraints (cheap text call).
2. **Extract**: the vision model lists every feature it observes in the image
   (chain-of-thought), *before* judging.
3. **Compare**: map observed features to each constraint → pass/fail + reason.
4. **Score**: fraction passed; report **faithfulness** (matches the request)
   separately from **factuality** (respects conventions, e.g. O red / N blue).
Use a strong vision model as judge; make the judge model configurable and record
which judge produced each verdict (the judge is itself a model — provenance
matters). **Exit criterion:** stable verdicts on a fixed image+rubric across runs
(report judge self-variance).

### A2. Wire into the runner
The `visual_rubric` branch already elicits a scene plan; extend it to
`render_scene → vlm.score`. Add a `Component 2` section to the scorecard and
leaderboard (per-criterion pass rates). Keep it behind the `execute` extra so the
core stays browser-free.

### A3. Component-2 corpus (~15–20 tasks)
Author high-quality visual tasks of the "mechanism / interaction / allostery"
class, each with an explicit decomposed rubric (3–5 constraints). Seed ideas from
the parked `data/molviewstories/` captions (curate, don't ingest raw) and classic
cases (haemoglobin proximal-His bond, p53–DNA interface, an enzyme catalytic
triad). Store rubric + an acceptable reference scene per task.

### A4. Judge validation (needed for the paper)
Small **human-agreement study**: a human rates N rendered images against the
rubrics; compute agreement (e.g. Cohen's κ) between human and VLM judge. Report it
— a VLM judge is only credible with a measured agreement number.

**Built (2026-10-19).** `scripts/build_rating_set.py` turns the pairs the judge saw in
the 2026-10-18 spec run (229 of 237; the 8 shown with their verdict on the public
gallery are left out) into a blind rating set (opaque ids; the model and verdict
stay in a private key under `results/a4/`), plus 12 known-same checks (T1 rescues) and
12 known-different checks (two references on different structures). Volunteers rate
them on the evaluator site's `rate.html` (molstar-chat-driver), two raters per pair.
`scripts/agreement.py` reports human-human Fleiss' κ, human-vs-judge Cohen's κ, and
rescue precision (of the judge's "same" calls, how many humans agree), after dropping
raters who fail the checks.

**Phase-A risks:** headless-render reliability (mitigate: render-complete signal +
retries + a golden-image regression test); judge variance/bias (mitigate:
strong judge, structured protocol, self-variance reporting); rubric quality
(mitigate: human review of rubrics).

---

## Phase B — sharpen Component 1

* **B1. Selection-accuracy sub-metric.** Single-residue clinical tasks floor at
  ~0.5–0.67 because the `polymer cartoon` scaffold dominates F1. Add a metric that
  isolates "did you select the right residues" from scene scaffolding, and report
  it for the grounded/clinical tiers. Re-score the clinical regime.
* **B2. Interaction/interface task type** (ChatMol-inspired; named-atom H-bond and
  computed-interaction tasks STARTED, see R3). Use gemmi neighbour
  search to extract interface/contact residues (ligand–protein, protein–protein),
  giving grounded "show the binding-site residues" / "show the PPI interface"
  tasks — a realistic, high-value class we currently lack.
* **B4. Entry resolution (STARTED — `tasks/mvs_resolve/`).** Every task used to hand
  the model the PDB id; real users name the protein. The first live failure was
  "a structure of PDE5A" → PDB 1UJ7 (does not exist), and probing found real ids
  for the wrong protein too. Six tasks now grade against *all* entries for the
  protein's UniProt accession (`accepted_ids`, folded by the grader). Next: more
  targets, and an `exists` sub-metric (did the id resolve at RCSB at all?) — a
  hallucinated id and a wrong-but-real id are different failures.
* **B5. Colour schemes (PARTLY DONE).** The Spec reference now teaches Mol*'s
  `custom.molstar_color_theme_name` on a `color` node, and the grader scores the
  theme instead of the placeholder colour. Still missing: treating a theme-coloured
  representation as equivalent to the per-chain components it would replace.
* **B6. Structured outputs.** Constrained decoding (`response_format: json_schema`,
  `strict`) with a trimmed MVS schema makes invalid trees impossible by
  construction. Measure validation failures + F1 against the prompt-only path on
  the cheap models.
* **B3. Corpus scaling & de-correlation.** More clinical targets (BRCA1, CFTR,
  kinases, more p53 structures incl. one with a numbering *offset* to exercise the
  SIFTS bridge); more Tier-1 template diversity so per-skill items are less
  correlated (the current 7×6 grid inflates n without independence).

---

## Escalating C1 grader (built; T1 made strict 2026-10-18 — see Phase A status)

Cost-cascading grader so we only pay for expensive grading when needed
(`molbench/escalate.py`):

* **T0 tree-match** (free) → `correct` if F1 ≥ threshold.
* **T1 visual diff** (`molbench/render.py` + `molbench/visual.py`, cheap) → render
  reference & prediction, pixel-diff; `rendering-equivalent` if near-identical.
  *Rescues `all` vs `polymer` etc. that tree-match under-scores* (demonstrated:
  tree F1 0.78 → visual_sim 1.0 → rescued).
* **T2 VLM judge** (`AnthropicImagePairJudge`, expensive) → semantic "same/different"
  on the image pair, ignoring camera. *Rescues same-scene-different-angle*
  (demonstrated: visual_sim 0.70 → VLM "same" 0.85). Also concentrates human review
  on the genuinely-ambiguous T2 cases only.

## Benchmark the grader (meta-evaluation)  ← TODO

The grader is a system with its own error rate; validate it against ground truth.

* **Positive control — `c1-identical-mvs`:** identical trees MUST render to
  identical images (visual_sim ≈ 1.0) and be judged "same" — calibrates the T1
  threshold and is a regression guard.
* **Hard positives:** hand-built semantically-equivalent pairs (selector synonyms,
  numbering aliases, child reordering, camera-only changes) that MUST be rescued at
  T1 or T2.
* **Negatives:** wrong colour / missing component / wrong structure pairs that MUST
  NOT be rescued.
* **Metric:** grader precision/recall on this control set; for T2, human-agreement
  (κ) on the verdicts. Report it — a rescuing grader is only trustworthy with a
  measured false-rescue rate.

## Phase C — rigor & paper-readiness

* **C1. Human-agreement studies** for both the C1 grader (does tree-match F1 track
  human judgement of correctness?) and the C2 judge (A4).
* **C2. Error taxonomy** mined from the new per-run archives (`runs/*.json` +
  `inspect_run.py`): capability vs formatting failures, per regime, per model.
* **C3. Expanded model panel + frozen final results** for the Results section.
* **C4. Methodology write-ups** of the data-driven course corrections
  (MolViewStories captions under-determined; "all pathogenic" = 204 residues;
  brittle-grader fix) — these are honest, citable lessons.

---

## Suggested sequence

*Superseded in part by the revised plan at the top: R5 → R6 → R7 come first.*

1. **A0 renderer** (unblocks everything visual) → **A1 judge** → **A2 wire-in**
   → **A3 corpus** → **A4 validation**. This delivers a working Component 2.
2. In parallel / between: **B1 selection-accuracy** (cheap, sharpens current
   results) and **B2 interface tasks** (extends grounding).
3. Then **Phase C** to harden for submission (JCIM / Digital Discovery; stretch
   NeurIPS D&B per `paper/venues.md`).

The single highest-leverage next step is **A0 (the renderer)** — it is the gate
for the entire visual half of the benchmark and the part most likely to surprise
us technically, so we de-risk it first.
