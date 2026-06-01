# MolBench — Methods

## 1. Overview

MolBench evaluates whether language models ("computational-intelligence assistants")
can translate natural-language requests into correct control of a molecular
visualization engine. It is organised as two components. **Component 1** measures
*executable correctness*: the model emits a structured scene specification that is
graded deterministically against a reference, without rendering. **Component 2**
measures *visual–semantic adequacy* for open-ended requests ("show the key
hydrogen bond") by rendering the model's scene and scoring the image against a
rubric with a vision–language judge. This paper focuses on Component 1, which is
fully implemented; the Component-2 interface and a curated scene corpus are
provided as scaffolding.

## 2. Task representation

A central design decision is to grade a *viewer-neutral intermediate
representation* (IR) rather than free-form code, which would be brittle to
surface variation and viewer idiosyncrasies. We use two IRs:

* **MolViewSpec (MVS) scene trees (primary).** [MolViewSpec](https://molstar.org/mol-view-spec/)
  describes a scene as a tree of typed nodes — `download → parse → structure →
  component → representation → color` (with `focus`, `label`, etc.) — formalised by
  a public JSON schema and rendered by Mol\*. Grading the scene tree tests
  *visualization competence* independently of any one engine's API surface.
* **Imperative API calls (secondary).** A small canonical action list mapping 1:1
  onto the `ipymolstar.PDBeMolstar` widget (e.g. `load`, `set_visual_style`,
  `color`, `focus`). This "tool-control" track tests whether a model can drive a
  specific, widely-used viewer API.

For both IRs the target API reference is **vendored and frozen** in the repository
and serves a dual role: it is the in-context documentation supplied to the
model-under-test, and the authority the grader trusts. Freezing both pins scores
to a fixed specification so they remain comparable across time.

## 3. Task corpus and provenance

Component-1 tasks are organised into difficulty regimes that differ in how the
*reference answer key* is obtained. Critically, every reference is correct **by
construction or by extraction** — never hand-guessed — and the construction method
is recorded with each task.

**Tier 1 — templated translation.** The prompt fully specifies a generic
structural selector (a chain, residue range, ligand class, ion, or whole
polymer) together with a representation and colour; the reference MVS tree is
built with the official `molviewspec` builder. Because the prompt determines the
selector, these tasks isolate *natural-language → selector translation* and
require no external knowledge.

**Tier 2 — structure-grounded.** Identity selections ("the heme", "the disulfide
bonds") cannot be specified by the prompt alone; their references are *extracted
from the deposited structure* with [gemmi](https://gemmi.readthedocs.io/): ligand
component identifiers, disulfide bonds from `struct_conn`, and per-residue
identity. These tasks additionally probe structural-biology *knowledge*, since
the prompt names the feature but not the residues.

**Tier 3 — clinical / canonical-numbering.** References are resolved through a
multi-source pipeline: PDBe [SIFTS](https://www.ebi.ac.uk/pdbe/docs/sifts/) maps
between UniProt canonical numbering and structure author numbering — the
authoritative resolution of the otherwise ambiguous "residue *N*" — and the
[UniProt](https://www.uniprot.org/) Variation API supplies pathogenic variants
cross-referenced to [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/). This yields
tasks such as "highlight the residue affected by the *R175H* pathogenic variant",
whose answer key is the structural residue carrying a real clinical variant.

A small set of hand-authored scenes complements the generated tiers. Each task is
automatically tagged with **skill categories** derived from its reference tree
(e.g. `selection`, `multi-component`, `camera`, `surface`, `annotation`),
enabling per-skill analysis without manual labelling. All data sources are
permissively licensed and credited; references are frozen into task JSON so that
grading requires no network access.

## 4. Grading

### 4.1 Component 1 (scene trees)

A predicted scene is parsed to its root node and compared to the reference by a
**tree-matching** metric. Each tree is flattened to its multiset of root-to-leaf
paths; the meaning of a scene is the set of such paths (e.g. "polymer → cartoon →
grey"). Two paths are scored by **weighted position-wise segment agreement**:
aligned segments are compared, boilerplate nodes (`parse`, `structure`) are
down-weighted, and discriminating nodes (target structure, component selector,
representation, colour, focus) carry full weight. (An earlier longest-common-prefix
variant was rejected because an incidental upstream mismatch suppressed credit for
correct downstream styling.) Reference and predicted path sets are matched
greedily by descending similarity; we report precision (matched / predicted),
recall (matched / reference) and their harmonic mean **F1**.

Matching is made tolerant to semantically irrelevant variation through explicit
normalisation: scene metadata and timestamps are stripped; structure identifiers
are normalised across file variants (`1cbs` ≡ `1cbs_updated`); author and label
residue/chain numbering are treated on a common axis; colour names are folded
(`grey` ≡ `gray`); library-default parameters are ignored; and a multi-residue
*list* selector is treated as equivalent to the corresponding set of
single-residue components. The grader is itself unit-tested for calibration:
reference-vs-reference scores 1.0, clearly-wrong predictions score near 0, and
partial-credit cases fall in between.

### 4.2 Component 2 (visual rubric)

For under-determined requests, the model's scene is rendered to an image and
scored by a vision–language judge under a decompose-then-verify protocol: the
prompt is decomposed into discrete visual constraints, the judge first extracts
observed features and then checks them against each constraint, separating
*faithfulness* (matches the explicit request) from *factuality* (respects
established conventions). The render-and-judge interface is specified; wiring a
headless renderer and judge is future work.

## 5. Evaluation protocol

Each model receives a system prompt comprising fixed task instructions, the
vendored API reference for the relevant IR, and (for the imperative track) the
JSON schema; the user message is the task prompt. The model returns text from
which the structured specification is extracted and validated. Because language
models are stochastic, every task is evaluated over **N independent samples**
(default N = 3–5); we report the per-task mean and standard deviation and
aggregate to per-model means, so that differences can be read against sampling
noise rather than single draws. The harness also records token usage, monetary
cost at published per-token prices, and wall-clock latency per model.

## 6. Model harness

Models are accessed through a uniform `generate(system, user) → text` interface.
Adapters cover the Anthropic and OpenAI APIs; a single OpenAI-compatible adapter
additionally serves OpenRouter, Google Gemini (via its OpenAI-compatibility
endpoint) and any compatible host, so that adding a model is a configuration
string rather than code. A keyless rule-based baseline establishes a score floor
and allows the full pipeline (and continuous integration) to run without
credentials or cost. Malformed or schema-invalid output is scored as a failure
rather than retried, since first-attempt validity is itself a measured capability.

## 7. Reported metrics and reproducibility

We report, per model: overall and per-track mean F1, a **difficulty-regime
breakdown** (translation / grounded / clinical), a **per-skill** breakdown, and
cost and latency. All tasks, references, generators, grader, and the model harness
are released; results are rendered to a public static leaderboard. Continuous
integration runs the grader-calibration tests and the keyless baseline on every
change, ensuring the measuring instrument remains sound as the corpus grows.
