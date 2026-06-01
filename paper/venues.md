# Where to submit — analysis

## What we're selling (the contribution framing)

Not "another tool-use benchmark." The differentiators to lead with:

1. **Grounded, by-construction reference answers** across a *difficulty gradient*
   (translation → structure-grounded → clinical), where harder regimes
   discriminate models more — a methodology contribution, not just a dataset.
2. **Clinical-variant grounding**: tasks that bridge *clinical genetics
   (ClinVar/UniProt) → 3D structure*, resolved through SIFTS numbering. This is
   novel and headline-worthy; no existing molecular-viz benchmark does it.
3. **Engine-neutral grading** via MolViewSpec scene trees, so the benchmark
   outlives any one viewer's API.

## Tiered options

### A. Targeted workshop — fastest feedback, right community
- **Language + Molecules (L+M), ACL-colocated.** Exactly where ChatMol published;
  the precise audience. Low barrier, fast, builds visibility. Ideal first venue at
  current scale.
- **AI for Science / FM4Science workshops (NeurIPS / ICML / ICLR).** Broader ML
  audience; good for the "agents controlling scientific software" angle.

### B. Domain journal — the people who would *use* it
- **Journal of Chemical Information and Modeling (JCIM, ACS)** — LLM + molecular
  modeling sweet spot; strong, citable, right readership. *Top pick for an
  archival home.*
- **Digital Discovery (RSC)** — modern, open, AI-for-chemistry; reproducibility-
  friendly and fast-growing. Excellent fit.
- **Bioinformatics (Oxford)** — Application Note or original paper; wide
  structural-biology reach.
- **GigaScience / GigaByte** — if we foreground the reproducible benchmark+data
  artifact and public leaderboard.

### C. ML benchmark prestige — highest bar, highest reach
- **NeurIPS Datasets & Benchmarks Track** — the premier home for a new benchmark.
  Stretch goal. Needs the scaling below before it is competitive.
- **TMLR** — rolling, no page pressure, benchmark-friendly; a pragmatic
  high-quality alternative to a conference deadline.

## Honest gap analysis (current state vs. competitive submission)

| Need | Now | For workshop/journal (A/B) | For NeurIPS D&B (C) |
|---|---|---|---|
| Corpus size/diversity | ~70 tasks, few proteins | enough with modest growth | hundreds–thousands, many proteins/folds |
| Component 2 (VLM-judged) | scaffolded | nice-to-have | required (the novel hard part) |
| Grader validation | unit-calibrated | adequate | + human agreement study |
| Model coverage | ~8 | adequate | broad, incl. frontier |
| Analysis | regime/skill breakdowns | adequate | + error taxonomy, what-the-field-learns |

## Recommendation

- **Primary:** target **JCIM** or **Digital Discovery** as the archival venue —
  right audience, reasonable bar, lets us lead with the clinical-grounding novelty.
- **Parallel/fast:** submit a short version to **L+M** (or an AI4Science workshop)
  for early visibility and feedback.
- **Stretch:** **NeurIPS D&B / TMLR** *after* (i) scaling the corpus across many
  proteins and (ii) implementing Component 2 with a human-validated judge. That is
  the version with the broadest impact.
