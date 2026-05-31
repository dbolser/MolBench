# MolBench

[![CI](https://github.com/dbolser/MolBench/actions/workflows/ci.yml/badge.svg)](https://github.com/dbolser/MolBench/actions/workflows/ci.yml)
[![Leaderboard](https://img.shields.io/badge/leaderboard-live-blue)](https://dbolser.github.io/MolBench/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A molecular-visualization benchmark and harness for LLM-based assistants ("CI"
assistants). It measures whether a model can turn natural-language requests
("load HIV protease, hide the waters, focus the inhibitor") into correct calls
against a real molecular viewer — [`ipymolstar`](https://github.com/molstar/ipymolstar)'s
`PDBeMolstar` (Mol\*).

## Tracks

| Track | Tasks | What the model emits | How it's graded |
|---|---|---|---|
| **MVS scene tree** (primary) | `tasks/mvs/*.json` | A [MolViewSpec](https://molstar.org/mol-view-spec/) state tree as JSON | **Deterministic, no browser.** Tree-matching: precision/recall/F1 over root-to-leaf paths, tolerant of child order, default params, and equivalent selectors (`molbench/mvs.py`). Engine-agnostic — tests *visualization* competence, not one viewer's quirks. |
| **API calling** (secondary) | `tasks/api_calling/*.json` | A list of imperative `PDBeMolstar` *canonical actions* | Field-aware list matching (`molbench/grader.py`). Tests whether a model can drive *this specific widget*. |
| **Visual rubric** (Component 2) | `tasks/visual_rubric/*.json` | A scene plan (scored later from a render) | **VLM-judged.** Rendered to PNG, then a vision model scores it against a rubric. Interface scaffolded (`vlm_grader.py`); a stub keeps the harness runnable today. |

The **MVS track is the primary target** (v0.2). MVS separates *what the scene is*
from *which engine draws it*, so the same answer key works for Mol\*, ipymolstar,
or any MVS-aware viewer — and curated MVS corpora (MolViewStories, Proteopedia)
become a path to scaling the benchmark to hundreds of tasks. Reference scenes are
authored with the official `molviewspec` builder (`scripts/author_mvs_tasks.py`),
so ground truth is correct by construction.

## Quick start (zero credentials)

```bash
python -m molbench.runner --models baseline
```

This runs the keyless rule-based **baseline** over the whole corpus and writes
`results/scorecard.json`. The baseline exists to (a) prove the harness runs with
no setup and (b) give real models a floor to beat.

## Models & API keys

A "model" is selected with a **spec string** `provider:model-id` (or the bare word
`baseline`). Keys live in a `.env` file at the repo root, which the runner loads
automatically (no `python-dotenv` needed; exported shell vars override it).

```bash
cp .env.example .env        # then fill in only the providers you want
```

### Supported providers

| Spec | Example | Env var(s) | Install extra |
|---|---|---|---|
| `baseline` | `baseline` | — (keyless) | none |
| `anthropic:<id>` | `anthropic:claude-opus-4-8`<br>`anthropic:claude-haiku-4-5-20251001` | `ANTHROPIC_API_KEY` | `.[anthropic]` |
| `openai:<id>` | `openai:gpt-4o` | `OPENAI_API_KEY` | `.[openai]` |
| `openrouter:<vendor>/<id>` | `openrouter:qwen/qwen-2.5-72b-instruct`<br>`openrouter:meta-llama/llama-3.3-70b-instruct` | `OPENROUTER_API_KEY` | `.[openai]` |
| any OpenAI-compatible host | `openai:llama3.1` (+ `OPENAI_BASE_URL`) | `OPENAI_API_KEY`, `OPENAI_BASE_URL` | `.[openai]` |

> **Why so few adapters?** OpenRouter, Together, Groq, DeepInfra and local
> Ollama/vLLM all speak the OpenAI wire format, so the single `openai:` adapter
> covers them via `OPENAI_BASE_URL`. OpenRouter alone unlocks Qwen, Llama,
> DeepSeek, Mistral, Gemini, Claude, GPT… behind one key.

### Run half a dozen models

```bash
pip install -e ".[all]"          # anthropic + openai SDKs
# (edit .env with the keys you have)
python -m molbench.runner --models \
    baseline \
    anthropic:claude-opus-4-8 \
    anthropic:claude-haiku-4-5-20251001 \
    openai:gpt-4o \
    openrouter:qwen/qwen-2.5-72b-instruct \
    openrouter:meta-llama/llama-3.3-70b-instruct
```

Each model gets a column in the scorecard. Filter the corpus with
`--categories api_calling` while iterating.

### Adding a provider

If a host isn't OpenAI-compatible, add ~6 lines: write an adapter implementing
`generate(system, user) -> str` in `molbench/models.py`, then register a `provider:`
branch in `build_model()`. That's the entire contract.

## CI & publishing results

* **CI** (`.github/workflows/ci.yml`) runs on every push: sanity tests + the
  keyless baseline on Python 3.10 and 3.12. It needs **no API keys** and spends
  nothing — it validates the harness, not the models.
* **Leaderboard** ([dbolser.github.io/MolBench](https://dbolser.github.io/MolBench/))
  is served from `docs/` via GitHub Pages. Publishing a result is a deliberate step:

  ```bash
  python -m molbench.runner --models baseline anthropic:claude-haiku-4-5   # run
  python scripts/build_leaderboard.py                                      # render docs/
  git add docs/ && git commit -m "results: <when/what>" && git push        # publish
  ```

  Real model results are never produced in CI (that would need secrets + spend),
  so the published leaderboard only ever shows runs you chose to commit.

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
