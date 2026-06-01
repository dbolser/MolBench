# MolBench — next-phase plan

Status: Component 1 (deterministic scene-spec grading) is implemented across three
grounded task regimes with an 8-model leaderboard. The next phase makes the
benchmark *complete and publishable*: implement Component 2 (visual grading),
sharpen Component 1, and validate the instrument.

---

## Phase A — Component 2: render + VLM judge  ← the headline

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
* **B2. Interaction/interface task type** (ChatMol-inspired). Use gemmi neighbour
  search to extract interface/contact residues (ligand–protein, protein–protein),
  giving grounded "show the binding-site residues" / "show the PPI interface"
  tasks — a realistic, high-value class we currently lack.
* **B3. Corpus scaling & de-correlation.** More clinical targets (BRCA1, CFTR,
  kinases, more p53 structures incl. one with a numbering *offset* to exercise the
  SIFTS bridge); more Tier-1 template diversity so per-skill items are less
  correlated (the current 7×6 grid inflates n without independence).

---

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

1. **A0 renderer** (unblocks everything visual) → **A1 judge** → **A2 wire-in**
   → **A3 corpus** → **A4 validation**. This delivers a working Component 2.
2. In parallel / between: **B1 selection-accuracy** (cheap, sharpens current
   results) and **B2 interface tasks** (extends grounding).
3. Then **Phase C** to harden for submission (JCIM / Digital Discovery; stretch
   NeurIPS D&B per `paper/venues.md`).

The single highest-leverage next step is **A0 (the renderer)** — it is the gate
for the entire visual half of the benchmark and the part most likely to surprise
us technically, so we de-risk it first.
