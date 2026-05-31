# MolBench

A molecular-visualization benchmark and harness for LLM-based assistants ("CI"
assistants). It measures whether a model can turn natural-language requests
("load HIV protease, hide the waters, focus the inhibitor") into correct calls
against a real molecular viewer — [`ipymolstar`](https://github.com/molstar/ipymolstar)'s
`PDBeMolstar` (Mol\*).

## Two components

| Component | Tasks | How it's graded |
|---|---|---|
| **1. API calling** | `tasks/api_calling/*.json` | **Deterministic, no browser.** The model emits a JSON list of *canonical actions*; we compare it to a reference with a tolerant, field-aware grader (precision / recall / F1). |
| **2. Visual rubric** | `tasks/visual_rubric/*.json` | **VLM-judged.** Tasks like "show the key H-bond in haemoglobin" are rendered, then a vision model scores the image against a rubric. The render+judge interface is scaffolded (`vlm_grader.py`, `adapter.py`); a stub keeps the harness runnable today. |

## Quick start (zero credentials)

```bash
python -m molbench.runner --models baseline
```

This runs the keyless rule-based **baseline** over the whole corpus and writes
`results/scorecard.json`. The baseline exists to (a) prove the harness runs with
no setup and (b) give real models a floor to beat.

## Plugging in real models

```bash
pip install -e ".[anthropic]"   # or .[openai] / .[all]
export ANTHROPIC_API_KEY=...
python -m molbench.runner --models baseline anthropic:claude-opus-4-8
python -m molbench.runner --models openai:gpt-4o --categories api_calling
```

A "model" is anything implementing `generate(system, user) -> str` (see
`molbench/models.py`). Add an adapter to benchmark a new provider.

## How it fits together

```
tasks/*.json ──┐
               ├─> runner.build_system_prompt()  (instructions + api_reference.md + JSON schema)
prompts/ ──────┘            │
                            ▼
                   model.generate(system, prompt)  ──>  raw text
                            │
                   extract_actions()  ──>  [canonical actions]
                            │
        ┌───────────────────┴────────────────────┐
   api_calling                              visual_rubric
   grader.grade(ref, pred)            adapter.apply_actions(view) ─> PNG ─> vlm_grader
   -> precision/recall/F1                    -> rubric pass/fail
```

## Key design choices

* **Canonical action IR** (`molbench/schema.py`) instead of grading raw Python.
  Viewer-neutral, browser-free grading, and re-targetable to Mol\* JS / PyMOL later.
  Every action maps 1:1 onto a real `PDBeMolstar` call — see `molbench/adapter.py`.
* **Vendored, frozen API reference** (`molbench/api_reference.md`) is both the
  context shown to the model and the grading authority. Pin a new snapshot rather
  than editing it, so scores stay comparable over time.
* **Tolerant grading** (`molbench/grader.py`): Jaccard over residue/chain locators
  with partial credit for styling, so "right residues, wrong colour" still scores.

## Layout

```
molbench/
  schema.py         canonical action schema + validator (single source of truth)
  api_reference.md  vendored PDBeMolstar API (frozen)
  models.py         baseline + Anthropic/OpenAI adapters
  grader.py         Component-1 structured grader
  adapter.py        canonical actions -> live ipymolstar calls
  vlm_grader.py     Component-2 VLM-judge interface + stub
  runner.py         load tasks, run models, write scorecard
prompts/system_api.md   model instructions (template)
tasks/                  the benchmark corpus
results/                scorecards (generated)
```

## Roadmap

* Headless render path (playwright + `adapter.apply_actions`) to feed real PNGs
  to the VLM judge.
* More tasks per skill; multiple reference answers per task; per-skill score
  breakdowns.
* Selection-equivalence via a structure-aware checker (resolve label vs author
  numbering against the actual mmCIF) instead of string-level tolerance.
```
