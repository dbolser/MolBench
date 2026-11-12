# Ledger of TODOs and ideas (2026-11-12)

Every TODO, idea, review finding and loose end raised in MolBench and its sibling
`molstar-chat-driver`, each with a proposed disposition against `FINAL_PLAN.md`.

**Dispositions**

- **IN** — a plan decision (D1–D16) or phase (A, B, C, final run) already covers it.
- **ADD** — not in the plan, should be; says where and roughly how much work.
- **LATER** — future work, with a one-line reason that can go in the paper.
- **DROP** — not worth doing, with the reason.
- **DONE** — already finished, with the evidence.

**What was swept.** MolBench: `ROADMAP.md`, `HANDOVER.md` (untracked, main checkout), `README.md`,
`paper/*`, code comments, tests, the 44 commit messages, PRs #1–#16 (bodies and inline review
comments), issues #4 and #5. Chat driver: `README.md`, `CLAUDE.md`, `TODO.md`, `site/SETUP.md`, code
comments, PRs #1–#25 (it has no issues). Memory notes for both projects. The 2026-11-06 audits and
the critique (the critique wins where they disagree). The private predecessor benchmark
`dbolser/molstar-llm-bench` (40 cases). The 237 real user turns on the preview site.

**Limits of this sweep (be aware).**

- About 100 inline bot review comments exist on MolBench PRs. I read the titles of all of them and
  the full text of about 20. I checked the current code for the ones listed below; the rest I
  assumed were handled in their PR and did not verify.
- Chat-driver PR inline review comments were not read (bodies only).
- Statuses describe the branch base (`8341e6f`). Other work packages are changing the same code now.
- "Scene produced" in the user data means the server returned a scene. It does not mean the scene
  was right. Whether Mol\* drew it is recorded for only 23 of 237 turns.

---

## 1. API track (imperative calls)

| id | item | source | type | disposition |
|---|---|---|---|---|
| L-001 | Task api-002's answer is the system prompt's worked example, word for word | audit_api §1; `prompts/system_api.md:31-41` | bug | IN — D10, D2. Replace the task, do not edit the prompt around it |
| L-002 | api-008 and api-019 use label numbering for author residues (trypsin triad is author 57/102/195) | audit_api §1 | bug | IN — D2 |
| L-003 | The vendored reference's own worked example teaches the same mistake (`residue_number` for "catalytic Asp25", only right because 1HVR has label = author numbering) | critique 1.5; `molbench/api_reference.md:89-96` | bug | ADD — api package, 30 min. D10 only says the example must not be a task; it must also not teach the numbering error. Prompt change, so do it before the final run |
| L-004 | api-016 cannot run as written (a UniProt id is not loadable; `alphafold_view` only colours). The reference doc line 21 is wrong too | audit_api §1 | bug | IN — D2. Also fix the doc line |
| L-005 | api-005 and api-014: superposition is PDBe's per-protein alignment view, not "align the globin subunits"; the two tasks are near-duplicates | audit_api §1 | bug | IN — D2, D14 |
| L-006 | api-009: "the A chain" of insulin 4INS is ambiguous (chains A and C are both A chains) | audit_api §1 | bug | IN — D2 (fix the prompt) or move it to the accept-set tier (D7) |
| L-007 | Named colours graded against hand-picked RGB values with ±8 tolerance; 0 of 16 models scored perfect on 5 tasks | audit_api §1; audit_health §6.1 | grading | IN — D2 |
| L-008 | api-015: 6VXX has one assembly, so `assembly_id` tests nothing | audit_api §1 | bug | IN — D2. Generator rule: assemblies only where they differ from the deposited model |
| L-009 | Grader pools author and label residue numbers, and author and label chain ids | audit_api §2; `molbench/grader.py:35` | grading | IN — D2 |
| L-010 | Grader ignores action order and `keep_colors` (two different end states score the same) | audit_api §2 | grading | IN — D2 (state replay) |
| L-011 | Grader ignores `uniprot_*` selection keys (any UniProt selection matches any other) | audit_api §2 | grading | IN — D2, D4 |
| L-012 | Equivalent answers are penalised: hex or named colours, `alphafold_view` as a property, `focus: true` inside the colour call, highlight/select colour traits | audit_api §2 | grading | IN — D2. ADD a test that pins each of these equivalences (api package, 2 h) |
| L-013 | API tasks store `skills`, the runner reads `categories`, so the by-skill table is empty. First raised in PR #1 review (July), never fixed | PR #1 inline; audit_api §2 | bug | IN — plan audit findings |
| L-014 | A keyword script with no model scores 0.715; models score 0.72–0.95. Load plus a global style alone scores 0.69 | audit_api §2–3 | grading | IN — D1 (task success), D2 |
| L-015 | The top 9 models cannot be told apart on 20 tasks | audit_api §3 | analysis | IN — D2 (~150 tasks), D12 |
| L-016 | Parts of the viewer surface are never tested: `highlight`, `clear_*`, several hide toggles, `preset`, `custom_data`, residue ranges, `entity_id`, `struct_asym_id`, `uniprot_*` | audit_api §1 | task idea | IN — D2 generator. ADD a coverage table (surface item × number of tasks) to the corpus freeze so gaps are visible (api package, 1 h) |
| L-017 | Real ipymolstar options left out of the vendored reference: `ligand_view`, `superposition_params`, `map_settings`, `sequence_panel`, author-numbered range keys | audit_api §1, §5D | task idea | ADD a decision, api package. Minimum: one Methods sentence listing what the frozen surface leaves out. Adding `ligand_view` and `superposition_params` is about half a day |
| L-018 | Tool-only tasks must be worded by intent ("show where the model fits the density poorly"), not by naming the feature, or they stay 16/16 transcription | audit_api §5D | task idea | ADD — rule for the API generator in phase B, no extra effort |
| L-019 | "The ligand" without its code: the API has no generic ligand selector, MVS has one, so the twin is lopsided and tests recall | critique §4 | task idea | DROP from the paired set — it would compare what each surface offers, not the model. Keep it MVS-only |
| L-020 | Clinical twins are confounded: the PDBe viewer maps UniProt numbers itself, MVS cannot | critique 1.4 | analysis | IN — D3 (flagged) |
| L-021 | The API track has no grounding-pack condition | critique §4 | analysis | ADD a one-line decision. D10 says "lookup tiers only" without naming the track. Proposal: MVS only, say so in Methods |
| L-022 | Print the action schema compactly in the prompt (saves about 900 tokens per call) | audit_api §5A | infra | ADD — runner or api package, 1 h, before the final run |
| L-023 | Schema errors are recorded but never affect the score or any table | audit_api §2; `runner.py:209-213` | grading | ADD — report an API "valid call list" rate next to the MVS valid-scene rate (D11 says validity is reported). 1–2 h |
| L-024 | The API parser takes everything from the first `[` to the last `]` | audit_api §2; `runner.py:157-173` | bug | ADD — tests with prose around the list and with two lists; runner package, 1 h |
| L-025 | `reset` is documented as `reset(data)` but references and grader use flat keys | PR #1 inline (Gemini); still so: `api_reference.md:56`, task 020 | bug | ADD — make the doc and the schema agree in the D2 rebuild, 30 min |
| L-026 | July API runs were not archived; only the best of 3 samples survives, so old means cannot be rebuilt | audit_api §3; HANDOVER:45 | infra | IN — D12, final run. Until then the paper gives no API numbers (critique 1.8) |
| L-027 | PR #1 claimed every API task "targets an operation a static scene cannot express"; false for 13 of 20 | audit_api §1 | paper | IN — D14 wording |
| L-028 | ROADMAP line 24: distance selection and arbitrary superposition "stay in the API track"; the PDBe viewer cannot do them either | audit_related §3 | paper | IN — D14 |
| L-029 | State replay must be checked against the real pdbe-molstar 3.3.2 bundle in a headless browser, including one UniProt-addressed task (the viewer's own mapping source may differ from the frozen SIFTS table) | audit_api §5A; critique §4 | grading | ADD — see plan gap G2. D2 says "follows 3.3.2 semantics" but not how that is proven. About 1 day |
| L-030 | Atom tables missing for 8 API entries and the AlphaFold model; tables have no UniProt column | critique 1.6 | infra | IN — D5, D4 |
| L-031 | `molbench/sifts.py` calls the PDBe API live with no cache | critique §4 | infra | IN — D4 (frozen SIFTS) |
| L-032 | API F1 is unrelated to MVS F1 across models (r = 0.04) | audit_api §3 | analysis | ADD — recompute on the final run in `paper_tables.py`; free |
| L-033 | Prompt length differs between tracks (API about 4k tokens), which confounds the paired comparison for small models | verdict; ROADMAP R5 note | paper | ADD — one limitations sentence; report prompt tokens per track in the manifest |
| L-034 | Agentic tool-control track: an MCP server around the PDBe viewer plus a provider-neutral tool loop | HANDOVER "Parked"; memory (Oct state: "awaiting Dan's yes") | task idea | LATER — D9. Frozen lookups gave no lift, and tool-calling support differs across the model panel |
| L-035 | A richer target for what MVS cannot do (distance selection, superposition): Mol\* v6 command layer, PyMOL or ChimeraX | audit_related §3(d) | task idea | LATER — D14 |
| L-036 | The action format is "re-targetable to Mol\* JS / PyMOL later" | README:152 | product | LATER — same reason as L-035 |
| L-037 | Trajectory efficiency (how many calls a model needs) | planning brief PDF | grading | LATER — needs an agentic track. A free proxy (extra actions beyond the reference) could be a supplement column |

## 2. MVS track: grading

| id | item | source | type | disposition |
|---|---|---|---|---|
| L-040 | Selection-accuracy metric (B1): one-residue tasks floor at 0.5–0.67 because the grey cartoon dominates F1 | ROADMAP B1; memory | grading | ADD — see plan gap G4. Report "target selection" (overlap on the requested atoms only) for the lookup tiers. Half a day, free, works on archives |
| L-041 | `exists` metric (B4): a made-up PDB id and a real-but-wrong id are different failures | ROADMAP B4 | grading | ADD — phase A data layer: freeze the list of current PDB ids (free download), then a three-way outcome (accepted / real but wrong / does not exist). Half a day |
| L-042 | Colour themes (B5): a chain-id theme on one cartoon is not yet treated as equal to one coloured component per chain | ROADMAP B5 | grading | ADD — needed before any colour-by-chain task (seed S1). Either resolve both forms to per-atom colours or build the accept set by script. About 1 day |
| L-043 | Structured outputs (B6) | ROADMAP B6; chat-driver `TODO.md:5` | analysis | IN — D11 |
| L-044 | Outcome bar per model: correct first try / recovered by repair / wrong scene / invalid tree / unrecoverable; strict F1 primary, repaired F1 second | HANDOVER "Parked" | analysis | IN — D11 |
| L-045 | `json-repair` is not in `pyproject.toml` | HANDOVER "Loose ends"; audit_health §6.6 | infra | ADD — `uv add json-repair` in whichever package owns the counterfactual (runner or paper), 5 min |
| L-046 | Dan's rule: invalid JSON and invalid MVS stay separate in full detail somewhere; grouping is fine in overview tables | memory (Oct state) | paper | IN — D11. Keep the five outcomes in a supplement table |
| L-047 | "Task success = final state exactly right" is not defined for harmless differences: `all` vs `polymer` under a cartoon draws the same picture (atom overlap 0.99); `ligand` in Mol\* also pulls in the bonded histidine; a model adds an unrequested extra | PR #10 body; ROADMAP R5 note; D1 | grading | ADD — see plan gap G1. Most important open definition in the plan |
| L-048 | Grader fallback to string matching for assemblies, symmetry, non-first models, `.pdb` files, `instance_id`, `structure_ref` | PR #10 body | grading | LATER — "assemblies and multi-model entries are out of scope; tasks use model 1 of the deposited unit". Real users do ask for them (U8) |
| L-049 | Validated F1 (render + VLM judge) stays a side column until the human study backs it | ROADMAP Phase A status | grading | IN — D8 |
| L-050 | The VLM judge looks lenient (called grey vs blue "same") | memory (Oct state) | grading | IN — D8, rating readout |
| L-051 | Rescue-only policy (a "different" verdict never zeroes a score) | memory (MolBench project) | grading | DONE — in `escalate.py` since June |
| L-052 | Pixel tier gave false rescues | ROADMAP Phase A | grading | DONE — PR #11 |
| L-053 | Benchmark the grader: a control set of identical pairs, hard positives (synonyms, numbering aliases, reordering) and negatives (wrong colour, missing part, wrong structure), with precision and recall | ROADMAP "Benchmark the grader ← TODO" | grading | ADD — see plan gap G3. 1–2 days, free at the atom-set level |
| L-054 | Does tree F1 track human judgement? (C1, first half) | ROADMAP C1 | analysis | ADD — rating readout (phase A): rating items already carry `tree_f1`; free |
| L-055 | Error taxonomy per regime and per model (C2) | ROADMAP C2 | analysis | ADD — `paper_tables.py`, about 1 day, free from archives. D11 covers validity only, not wrong-content errors (wrong chain, wrong residue, extra parts) |
| L-056 | Write up the data-driven course corrections (story captions under-determined; "all pathogenic" = 204 residues; brittle grader; overlapping-cartoon references found by a human rater) | ROADMAP C4; memory (working style) | paper | ADD — a short "what we got wrong" subsection, half a day |
| L-057 | Hidden lint counterfactual: 36 invalid-MVS samples are mostly `focus` under the wrong parent, which the chat driver fixes by rule | ROADMAP 2×2 result; chat-driver PR #15 | analysis | ADD (optional) — report how many invalid scenes a three-rule fixer recovers, beside the json-repair counterfactual. 2–3 h, free |
| L-058 | Empty reference selections on six templated tasks (ligands on entries with none) | PR #10 body | bug | DONE — those six files are gone (36 generated tasks remain). Keep the rule in the new generators: no task whose target is empty |
| L-059 | Overlapping-cartoon chain references; colour-node selectors ungraded | ROADMAP A4 note | bug | DONE — PR #16 |
| L-060 | Hotspot pack disagreed with the frozen reference | PR #9 inline (Codex) | bug | DONE — reference and pack now both give 215, 109, 281, 110, 239, 241 |
| L-061 | The hotspot grounding pack hands over the answer (counts show the top six) | PR #9 body | analysis | ADD — exclude hotspot tasks from the grounding ablation, or report them apart. One line in `paper_tables.py` |
| L-062 | "Hotspot" defined as most ClinVar records gives 215/109/281/110/239/241 for p53, not the textbook hotspots (175, 245, 248, 249, 273, 282) | my reading of `tasks/mvs_clinical/hotspots-1tup.json`; not checked further | task idea | ADD — see plan gap G8. Reword ("most distinct pathogenic variant records") or drop the template from the clinical tier |
| L-063 | Grounding packs list every chain copy of a residue; references use one chain | PR #9 body and inline | grading | Partly DONE — prompts now name the chain. ADD a generator rule for the wider clinical tier: name the chain in the prompt, or accept every copy by script |
| L-064 | Resolve task accepted ids include fragments (isolated domains for "the CFTR channel") | PR #6 inline (Codex) | grading | Looks DONE for CFTR (24 accepted ids, 1XMI absent). ADD the coverage filter as a stated rule in the phase B resolve generator |
| L-065 | GFP prompt did not say which species | PR #6 inline | bug | DONE — prompt now says *Aequorea victoria* |
| L-066 | Accepted-id lists are a snapshot (fetched 2026-09-30); new entries appear weekly | `tasks/mvs_resolve/*` provenance | grading | ADD — re-fetch at corpus freeze, record the date in the manifest, state it in Methods. Ties to L-041 |
| L-067 | Escalation renders the canonical reference entry against the model's accepted alternative entry, so the pictures differ | PR #6 inline | grading | DROP — validated F1 is a side column (D8); note it as a known limit of that column |
| L-068 | A reference render failure must not zero the model's answer | PR #12 inline | bug | DONE — `failed_side` in `escalate.py:100`, `runner.py:378` |
| L-069 | Without `--validate`, parsed scenes must not be reported as valid | PR #12 inline | bug | DONE — outcome `unchecked` (`runner.py:225`). The final run must validate; put it in the manifest |
| L-070 | A scene that parses and validates but draws nothing (structure with no representation) | chat-driver PR #24 | grading | ADD — one test that such a scene scores 0 and fails task success; 30 min |
| L-071 | Skill tags: `annotation` is never produced; `resolve` is not derived from the tree | audit_paper §2 | paper | ADD — fix the Methods sentence, 10 min |
| L-072 | Single prediction that put `params` as a list crashed a whole run | PR #3 | bug | DONE — PR #3, regression test |
| L-073 | Re-running a task generator drops the grounding pack from the task file | PR #9 body | infra | IN — phase A data layer; a test already catches it. Keep the build order in the one-command corpus build |
| L-074 | Use the Jev decision model as a cheap judge of scenes (it added nothing as a JSON repairer) | memory (Jev note) | grading | LATER — a judge needs the human study first (D8) |
| L-075 | Small models lose validity as the prompt gets longer (spec reference 2.4× longer; packs longer again) | ROADMAP R5, 2×2 | analysis | IN — paper tables. State it as a finding and as the reason packs "hurt" |
| L-076 | Report all three grounding numbers (all models −0.041; valid-in-both −0.004; lookup tasks −0.021), not only the kind one | critique §2 | paper | ADD — wording rule for the paper package |
| L-077 | The bare condition ran on 3 models only; say so | critique §2 | paper | IN — D10 (3 models) |
| L-078 | "Harder tiers separate models more" is false on the overall score (validity swamps it) and true on valid scenes only | memory (MolBench project); audit_paper §3C | analysis | ADD — paper claim must use the valid-only tier table; already computed in the audit |

## 3. Corpus and task ideas

| id | item | source | type | disposition |
|---|---|---|---|---|
| L-080 | Clinical tier is 9 tasks on one protein where UniProt = author numbering | critique 1.4 | task idea | IN — D4 |
| L-081 | Clinical targets named so far: BRCA1, CFTR, kinases, more p53 entries with an offset | ROADMAP B3 | task idea | IN — D4. Add BRAF V600E: a real user asked for it (U7) |
| L-082 | Only 14 structures; the 7 × 6 template grid inflates n | ROADMAP B3; audit | task idea | IN — D5 |
| L-083 | More tier-1 template variety, not just more structures | ROADMAP B3 | task idea | ADD — phase B: at least the seeds in section (b). D5 fixes structures, not templates |
| L-084 | One phrasing per task; no paraphrase check | not raised before; reviewer question | analysis | ADD — see plan gap G6 |
| L-085 | Interface and binding-site tasks (B2): residues near a ligand, or between two chains, found by neighbour search | ROADMAP B2; predecessor comp-001, comp-005 | task idea | IN — phase B "interactions", if those templates are included. See seed S5 |
| L-086 | Name-the-protein tasks (B4): more targets | ROADMAP B4; PR #6 | task idea | IN — phase B "resolve" |
| L-087 | Follow-up turns: start scene in the task, graded on the final state | issue #5 | task idea | IN — D6 |
| L-088 | Follow-up failure modes to cover: clobbering, "it/that" referents, requests that should change nothing, names the user gave a component | issue #5 | task idea | IN — D6 for clobbering and referents. ADD the other two as templates (seeds S3, S10) |
| L-089 | Predecessor cases vis-007 (show a hidden component) and vis-008 (act on a user-named component) | issue #5 | task idea | ADD — vis-007 fits the API track (hide toggles hold state); vis-008 fits MVS (component `ref`). Two templates, about 2 h |
| L-090 | Ambiguous prompts: 7 seed prompts and a taxonomy (interpretation, vagueness, domain inference, synonym, negation, state query) | issue #4 | task idea | IN — D7 |
| L-091 | Ambiguous prompts graded by rubric or VLM | issue #4 | grading | LATER — D7 and D8 rule the judge out |
| L-092 | "No own-goal" floor: whatever the reading, the protein must still be visible and nothing asked-for removed | issue #4 | grading | ADD — to the D7 tier as a second deterministic number. 2–3 h |
| L-093 | A question is not an edit ("what structures do I have loaded?"): the right answer is no scene change | issue #4 amb-003; user data U10 | task idea | ADD — 2–3 tasks in the follow-up tier whose accepted final state is the start state. See plan gap G5 for how "no answer" is scored |
| L-094 | Trap prompts that reward asking for clarification | planning brief PDF | task idea | LATER — needs a dialogue judge. L-093 is the deterministic part |
| L-095 | Report the ambiguous tier as its own column, never averaged in | issue #4 | paper | IN — D7. State it in the table spec |
| L-096 | Predecessor benchmark: 40 cases to mine (hide helices / sheets / charged residues / first 20 residues / backbone / alpha carbons; everything except chain A; metal ions as spheres) | `dbolser/molstar-llm-bench` (private) | task idea | ADD — seeds S6, S7. Its answers target a retired tool API; only prompts port |
| L-097 | "Colour 7MO7 by chain" as a task (stresses many components and JSON length) | memory (preview site) | task idea | ADD — seed S1; needs L-042 |
| L-098 | Curated real user prompts become tasks; after that they are dev data for the chat driver | ROADMAP decision 2; `site/SETUP.md` §7 | task idea | ADD — seeds in section (b). Done once already (PR #6 resolve tasks) |
| L-099 | "Highlight all pathogenic residues" is 204 residues on p53, not a task | memory | task idea | DONE — replaced by single variants and counted hotspots |
| L-100 | MolViewStories captions as open-ended tasks | README; ROADMAP A3 | task idea | LATER — D8. 39 files stay parked in `data/molviewstories/` |
| L-101 | Other sources named for tasks: Proteopedia, PDBImages | planning brief PDF | task idea | LATER — references there are not built by script |
| L-102 | Loading local or custom files (`custom_data`) | planning brief PDF | task idea | Partly IN — the api-016 fix loads the AlphaFold model by URL. Local files: DROP, nothing to grade offline |
| L-103 | Camera checks (is the view centred on the target?) | planning brief PDF | grading | LATER — both tracks grade the focus target's atoms, not the camera pose |
| L-104 | Two structures at once, superposed ("haemoglobin and myoglobin, superimposed") | user data U9 | task idea | LATER — neither frozen surface computes a superposition (D14) |
| L-105 | `tasks/visual_rubric/` holds 2 tasks written as API actions that cannot be rendered | audit_health §4 | task idea | ADD — leave them out of `corpus-v1.0` counts and say so; 10 min |
| L-106 | Typed ids must be kept character for character (`1hh0` became `1HHO`) | chat-driver PR #24 | task idea | ADD — seed S9 |
| L-107 | Public repo since 2026-05-31 with every reference answer: later models may have seen the tasks | not raised before; reviewer question | paper | ADD — see plan gap G7 |

## 4. Open-ended tasks and the judges (Component 2)

| id | item | source | type | disposition |
|---|---|---|---|---|
| L-110 | Rubric judge with decompose → extract → compare → score, faithfulness vs factuality, judge self-variance | ROADMAP A1 | grading | LATER — D8 |
| L-111 | Wire the rubric path into the runner; per-criterion pass rates | ROADMAP A2; `runner.py:349` | infra | LATER — D8 |
| L-112 | 15–20 open-ended tasks with rubrics (proximal histidine, p53–DNA interface, catalytic triad) | ROADMAP A3 | task idea | LATER — D8 |
| L-113 | `paper/methods.md` says a "curated scene corpus" exists for this | audit_paper §2 | paper | IN — D15 rewrite |
| L-114 | Renderer golden-image regression test | ROADMAP Phase-A risks | infra | DONE — `tests/test_visual_tier.py` fixtures (PR #11) |
| L-115 | Pydantic AI: revisit for the rubric judge only | memory (MolBench project) | infra | LATER — with L-110 |
| L-116 | Human study: reach two raters per pair (about 119 more ratings); human–human agreement is unusable today (about 15 double-rated items) | audit_health §5 | analysis | IN — phase A rating readout, phase C final call |
| L-117 | `agreement.py` lacks confidence intervals, weighting for the over-sampled "same" pairs, and a way to exclude test tokens | audit_health §5 | analysis | IN — phase A rating readout (assumed; confirm with that package) |
| L-118 | CSV export turns `false` into a true flag in `agreement.py:111,113` | audit_health §5 | bug | ADD — rating package: parse booleans strictly, 15 min |
| L-119 | The first rater's known-same checks may be orphaned by the set trim, which would drop him under the attention-check rule | audit_health §5 | analysis | ADD — rating package: verify on the export before any number is quoted |
| L-120 | Which of the owner's two rating tokens is real: the first holds 62 real ratings; the second is test-only and has 0 rows | memory (Nov audit) | analysis | DONE — settled 2026-11-06 |
| L-121 | Delete trial ratings on the 9 re-rendered gen-chain items (pictures changed under the same ids) | chat-driver PR #23 "on merge" | bug | ADD — rating package: check it was done; the audit says the 18 gen-chain pairs got new ids, so it may be moot |
| L-122 | Rating set v2: two p53 one-residue pairs cannot be judged in a whole-complex render | ROADMAP A4 note | analysis | ADD — phase C rating set v2: zoom on the target for small selections |
| L-123 | A bigger study exists (SciVisAgentBench: 12 experts, r ≈ 0.81); present ours as validation, not a headline | audit_related §3 | paper | IN — D8 |
| L-124 | Standardised rating portal under MolBench: replay stored runs, about 5 prompts × 5 models per person, "failed / OK / could be better" | memory (evaluator harness; preview site "NEXT") | product | Partly DONE — the same/different rating page is live. The rest: LATER |
| L-125 | Head-to-head arena with preference ranking | memory (evaluator harness) | product | LATER |
| L-126 | Allowlist download hosts before stored model scenes are rendered in other people's browsers | memory (preview site, risk L1) | infra | LATER — only matters with L-124. The rating page shows JPEGs, so it is safe today |
| L-127 | A Mol\* load extension for grading overlays | memory (evaluator harness) | product | DROP — nothing uses it |

## 5. Runs, reproducibility and infrastructure

| id | item | source | type | disposition |
|---|---|---|---|---|
| L-130 | Always archive raw outputs; never `--no-archive` | memory; HANDOVER | infra | IN — rules, D12 |
| L-131 | Samples: Methods says 3–5, runs used 1 | audit_paper §2 | paper | IN — D12 |
| L-132 | No confidence intervals | audit | analysis | IN — D5 (clustered), D12 |
| L-133 | Temperature is "provider default" and so differs by model; truncated answers (hit the output limit) are counted as invalid JSON | D12; `models.py` | analysis | ADD — runner package: store temperature, max output tokens, finish reason, serving provider and the returned model id per sample; report truncation apart from malformed JSON. 2–3 h. See plan gap G9 |
| L-134 | mistral-small never ran on MVS (upstream rate limit, 11 attempts) | ROADMAP 2×2 gaps | infra | IN — final run manifest. ADD a retry-later list so one model cannot block the run |
| L-135 | Two models ran through OpenRouter instead of the makers' own APIs | ROADMAP 2×2 gaps | infra | IN — D13 manifest records the route |
| L-136 | 9 of 16 models have no price; cost column incomplete | audit_paper §2 | infra | IN — D13 (prices in the manifest) |
| L-137 | Latency numbers are from July | audit_paper §2 | analysis | ADD — record latency in the final run, or drop the column; runner, 30 min |
| L-138 | The qwen3-30b October archive was never written | ROADMAP 2×2 gaps | infra | DROP — the final run replaces it; footnote in any October table |
| L-139 | No frontier model in the panel | `paper/venues.md:49`; audit_api §6 | analysis | ADD a decision for the manifest — see plan gap G10 |
| L-140 | Hard-coded dates and task counts in `scripts/build_site_data.py` | audit_health §6.5 | infra | IN — plan audit findings |
| L-141 | CI runs 2 of 7 test files and installs with pip | audit_paper §2 | infra | IN — plan audit findings |
| L-142 | Raw runs and the rating key exist on one machine | audit_health §6.3 | infra | Partly DONE — `~/Backups/molbench-2026-11-12` is the same machine. ADD: off-machine copy, Dan's call |
| L-143 | No data release: `runs/` and `results/` are git-ignored, no DOI, no corpus version | audit_paper §3 | paper | Partly IN — D13 names a corpus version. ADD: deposit archives with a DOI and write the availability statement; see plan gap G11 |
| L-144 | Stale staging leaderboard is still served and calls itself "under review" | audit_health §3 | infra | ADD — delete `docs/staging/` when the site is rebuilt, 10 min |
| L-145 | Leaderboard Finding 04 is fixed text: "No other molecular-viz benchmark does this" | audit_health §6.5 | paper | ADD — "to our knowledge", backed by the related-work search |
| L-146 | ROADMAP is stale (says 8 models; old escalation counts; "next step A0"; R9 "todo") | audit_health §4 | infra | ADD — after merge, cut ROADMAP to a pointer to FINAL_PLAN and this ledger, 30 min |
| L-147 | README roadmap section lists three items that are done or deferred | `README.md:218-225` | infra | ADD — README refresh in phase C, 30 min |
| L-148 | `HANDOVER.md` was never committed; its open decisions were resolved by PR #8 | HANDOVER; audit_health §6.9 | infra | ADD — retire it; its parked items are L-034, L-044, L-045 here |
| L-149 | Promote staging to live; fix hard-coded Finding 03; transpose wide tables | HANDOVER | infra | DONE — PR #8, PR #12 |
| L-150 | New models need the tiered (render + judge) grading run | HANDOVER | infra | DONE — 2026-10-18 run, 15 models |
| L-151 | Seven merged remote branches never deleted | audit_health §1 | infra | ADD — tidy after the final-benchmark merge, 5 min |
| L-152 | Pillow `Image.getdata` is deprecated (removed October 2027) | audit_health §2; `molbench/visual.py:27` | infra | ADD — one-line fix, whoever owns `visual.py` |
| L-153 | Atom tables must ship inside the package | PR #10 inline | infra | DONE — `molbench/atom_tables/` |
| L-154 | OpenRouter spending caps are per key but the balance is per account; another project drained MolBench's | critique 1.3; memory | infra | ADD — final-run checklist for Dan: cap or move the other key before topping up |
| L-155 | Do not run MolBench on the chat site's keys | memory (OpenRouter accounts) | infra | ADD — conflicts with the plan's pilot; see contradiction C3 |
| L-156 | Supabase project pauses when idle; the keep-alive is on an unmerged chat-driver branch, deploy awaits Dan | memory; branch `feat/supabase-keepalive` | infra | ADD — must be live before the phase C "final call" to raters, or the rating page will be down |
| L-157 | The chat site's OpenRouter key expires 2027-03-28 | memory | product | LATER — product upkeep |
| L-158 | Untracked `supabase/` folder in the MolBench checkout; a second, paused Supabase project | HANDOVER; memory | infra | DROP — unrelated to the benchmark |
| L-159 | Mol\* versions differ: benchmark pins 5.9.0, the chat site loads 5.10.1, pdbe-molstar 3.3.2 bundles its own | chat-driver PR #6; D14 | paper | ADD — one Methods sentence naming all three |

## 6. Paper and positioning

| id | item | source | type | disposition |
|---|---|---|---|---|
| L-170 | No abstract, introduction, related work, results, discussion, limitations, figures or references | audit_paper §1 | paper | IN — phases A and C, D15 |
| L-171 | Related work to cite: ScienceBoard, SciVisAgentBench, OSWorld-Science, Speak to a Protein, ChimeraX MCP, ChatMol, MiSI-Bench, the two MolViewSpec papers, Vollmar et al. 2026 | audit_related §1–2 | paper | IN — phase A |
| L-172 | Motivating example: a hackathon tool's prompt says database residue numbers "are always author numbers"; 63.6% of entries differ | audit_related §2B | paper | ADD — one sentence in the introduction |
| L-173 | "Engine-neutral" needs its caveat: only Mol\* renders MVS, and selections follow Mol\* 5.9.0 rules | audit_related §3; memory | paper | ADD — say "graded at the specification level with frozen Mol\* semantics" |
| L-174 | The Mol\* team now has an in-viewer assistant with scene-checked tests; scoop risk | audit_related §2A | paper | IN — D15 (preprint first). Open question for Dan: contact them? |
| L-175 | `paper/venues.md` is stale (no later edition of the L+M workshop found; ICLR and NAACL 2027 workshops are about 2027-02-01) | audit_paper §5 | paper | ADD — update or delete in the paper package, 30 min |
| L-176 | NeurIPS Evaluations & Datasets needs hosted data and Croissant metadata | critique 1.10 | paper | LATER — May 2027 at the earliest. L-143 is the first step |
| L-177 | Other venues listed: Bioinformatics, GigaScience, TMLR | `paper/venues.md` | paper | LATER — after the JCIM / Digital Discovery decision |
| L-178 | Vocabulary: "CI", not "AI" | memory | paper | IN — D16 |
| L-179 | Licences, data-source credits, and a note on the volunteers (recorded with notice; prompts shown only in paraphrase) | README acknowledgements; `site/SETUP.md` | paper | ADD — see plan gap G12 |
| L-180 | Are the volunteer raters co-authors or acknowledged? | verdict "decisions for Dan" | paper | Open question for Dan |
| L-181 | Human baseline (an expert doing the tasks) | not raised before; ScienceBoard reports one | analysis | LATER — "references are built from the structure, so a human baseline measures effort, not correctness" |
| L-182 | Cost per model (best open model beat the best closed one at 7× lower cost in October) | leaderboard Finding 02 | analysis | IN — D13 prices; recompute after the run |

## 7. Chat driver and product items (listed so nothing is lost)

| id | item | source | type | disposition |
|---|---|---|---|---|
| L-190 | Per-turn thumbs for grading real traffic (R9) | ROADMAP R9 "todo" | product | DONE — five-level reactions since chat-driver PR #7; 26 turns carry one |
| L-191 | Product claims should come from real prompts that arrive after a prompt version is frozen | ROADMAP decision 2 | analysis | LATER — too little traffic (about 12 turns a month) |
| L-192 | The chat driver's prompt drifted from MolBench's ("port back if it helps") | chat-driver PR #15 | product | DROP for the benchmark — D10 forbids tuning. The shared reference was re-synced in PR #18 |
| L-193 | Re-sync the chat driver's vendored reference after the final corpus freeze | chat-driver `CLAUDE.md`; `scripts/sync-prompt.mjs` | product | LATER — 5 min after the freeze |
| L-194 | Move the reference backend into MolBench as `molbench/serve.py` | chat-driver PR #4 | product | LATER |
| L-195 | Follow-up prompt buttons | memory "TODO #11" | product | DONE — chat-driver PR #14 |
| L-196 | Server-side fixes that mask model errors (JSON repair, re-parenting, colour-scheme mapping, id grounding, empty-selection check) | chat-driver PRs #13, #15, #16, #18, #24 | analysis | IN as counterfactuals — L-044, L-057. They also explain why live success is higher than benchmark validity; one Discussion sentence |
| L-197 | Residual security notes (feedback ownership, model-error passthrough) | memory (preview site) | product | DROP for the benchmark |
| L-198 | Live tool calls for lookups (PDB, SIFTS, ClinVar) behind the same contract | memory (evaluator harness) | product | LATER — D9 |

---

## (a) Plan gaps a reviewer would raise

Ordered by how much they could hurt the paper.

- **G1. "Exactly right" is undefined (L-047).** Task success is a headline metric (D1), but the plan
  does not say which differences are harmless. Three known cases: `all` vs `polymer` under a cartoon
  (same picture, different atoms), Mol\*'s `ligand` including a bonded residue, and unrequested
  extras. Proposal: compare what is drawn (per atom: representation and colour), decide once whether
  extras fail, and pin each case with a test. About 1 day. Without it task success will be near zero
  for reasons a reviewer will call unfair.
- **G2. The API replay is not proven against the real viewer (L-029).** A Python port of the
  viewer's selection rules is only as good as its check. Run every reference, plus a sample of model
  answers, in the pinned pdbe-molstar 3.3.2 bundle and compare atom sets, the way the MVS atom tables
  were checked against Mol\* (529 pairs). About 1 day. Could not find this step in the plan.
- **G3. No measured error rate for the grader (L-053).** The roadmap's control set (identical pairs,
  equivalent pairs that must pass, wrong pairs that must fail) was never built. 1–2 days, free.
- **G4. One-residue tasks are scored mostly on the scaffold (L-040).** On the clinical tier the
  grey cartoon is most of F1. The widened clinical tier is the lead claim, so it needs a score for
  the requested atoms alone.
- **G5. No way to score "should not have answered".** Questions, impossible requests (spin; select
  by distance in MVS) and no-op follow-ups have a right answer of "no change". Today any non-scene
  is `invalid` and scores 0. The follow-up tier can express it as "final state = start state", but
  the runner needs an agreed way for a model to say "no change". Decide before corpus freeze.
- **G6. One phrasing per task (L-084).** Add 2–3 scripted paraphrases for a subset (about 30 tasks),
  or state it as a limitation. Real users phrase tersely ("spacefill", "hide water").
- **G7. Contamination (L-107).** Tasks and answers have been public since May 2026. State it. The
  by-script generators are the answer: a fresh structure panel can be drawn at any time; consider
  holding back a small unpublished split.
- **G8. Clinical references must survive a domain expert (L-062, L-063).** "Hotspots by ClinVar
  record count" is not what a p53 biologist means by hotspot. Check each clinical template's wording
  against what the script actually computes.
- **G9. Sampling settings are uncontrolled (L-133).** Record temperature, output-token limit, finish
  reason and serving provider per sample; report truncation separately from malformed output.
- **G10. Model panel has no frontier model (L-139)** and the plan does not say how the panel was
  chosen. Add a selection rule and at least one frontier model, or say why not (cost: unverified
  estimates of $3–14 per sample pass).
- **G11. Data availability (L-143).** One manifest is not a release. Deposit corpus, archives and
  tables with a DOI; say what is withheld (the rating key until the study closes).
- **G12. People (L-179, L-180).** A short statement on the volunteers (informed that prompts are
  recorded; no personal data released) and the authorship decision.
- **G13. Related-work claims on the site (L-145)** and the "engine-neutral" wording (L-173) should
  match what the paper can defend.

## (b) Task template seeds

From the 237 real user turns (5 invite tokens; two of them account for 227 turns, and one of those
two looks like the project's own testing — not verified) and from earlier ideas. Counts come from
keyword matching, so they are approximate and overlap. 29 of 237 turns returned no scene. 26 turns
have a reaction: 13 negative, 6 positive, 5 neutral, 2 blank. 162 turns are follow-ups within a
session.

**What real users asked for**

| id | kind of request | turns (no scene) | paraphrased examples | what went wrong |
|---|---|---|---|---|
| U1 | Colour by chain or subunit on a multi-chain entry | ~26 (3) | "colour by chain"; "each alpha a shade of red, each beta a shade of blue"; "colour the three chains red, orange and green" | Long multi-component JSON with missing brackets; the first outside evaluator hit this |
| U2 | Name a protein, no id | ~38 (0) | "I want to see a structure of PDE5A"; "a virus capsid"; "any heterodimer"; "crab myoglobin" | Made-up id; real id of the wrong protein; a monomer for "heterodimer". 4 negative reactions |
| U3 | Select by distance or contact | ~25 (3) | "residues within 5 Å of the magnesium"; "water close to chain C"; "the histidine close to the haem" | MVS has no distance selector; a scene still came back for most (correctness unknown); one failed to render |
| U4 | Draw a hydrogen bond or a named contact | ~12 (2) | "show the key H-bond in oxygen-bound myoglobin"; "turn on the H-bond between haem and histidine" | Wrong histidine chosen; "not supported" reply before the reference was fixed. 3 negative reactions |
| U5 | Colour schemes | ~22 (2) | "rainbow cartoon"; "colour by secondary structure"; "colour ligands by atom type"; "colour residues by index" | Scheme names used as colours (render error) |
| U6 | Ranges given as terse specs | ~39 (1) | "chain A, residues 26–35, red, label 'epitope 6'" (several per prompt); "colour the motif PA blue" | Mostly produced scenes; correctness unknown. Sequence-motif lookup needs the sequence |
| U7 | Variants and single residues | ~10 | "show the BRAF V600E mutation"; "highlight residue 600"; "zoom in on residue 4" | Unknown; the clinical tier's home ground |
| U8 | Assemblies, symmetry, one copy | ~10 (1) | "expand the symmetry"; "load it as a monomer"; "restrict to one subunit" | Empty viewer for "as a monomer"; 1 negative reaction |
| U9 | Two structures, superposed | 2 | "haemoglobin and myoglobin, superimposed" | Not expressible |
| U10 | Questions | 3 (3, correctly) | "what is loaded?"; "is there a water touching those ions?" | Answered from the model's memory of the id, not the scene (wrong protein named) |
| U11 | Follow-up edits with a referent | most of 162 | "colour it red"; "hide the label"; "the other parts should be grey"; "that's better" | Before scene context: asked for clarification. After: one failure cascaded through the session |
| U12 | Motion | 4 (4) | "spin the scene"; "rotate 90 degrees about x" | Not expressible in MVS; API track has spin |
| U13 | Hide, show, keep only | ~19 (4) | "hide water"; "hide everything except chain C"; "remove half the waters"; "hide water except 72 to 78" | Odd subsets fail; 1 negative reaction on plain "hide water" |
| U14 | Representation names | ~61 (3) | "wireframe"; "trace"; "tube"; "rope"; "licorice"; "make the iron a big ball" | User reported that wireframe, trace and tube all came back as cartoon; atom size is not settable |
| U15 | Typed id, nothing else | 7 (0) | "load 1hh0" | Model changed the id to a famous look-alike. 2 negative reactions |
| U16 | AlphaFold model by accession | ~7 (1) | "load the AlphaFold model for <accession>" | Unknown |
| U17 | Labels | ~24 (2) | "label every residue in the range with its name and number"; "add annotations from UniProt" | UniProt annotations are a lookup, not in either surface |

**Seeds, each with a by-script reference**

| seed | template | from | reference by construction |
|---|---|---|---|
| S1 | Colour each chain differently on an entry with ≥ 4 chains; variants: named colour per chain; "alpha chains reds, beta chains blues" | U1, L-097 | Chains from `_atom_site`; entity-to-chain map from the mmCIF for alpha/beta. Accept the chain-id theme and any assignment of distinct colours when none are named (accept set by script; needs L-042). API twin: one `color` entry per `struct_asym_id` |
| S2 | Name the protein, optionally with a state ("oxygen-bound haemoglobin", "a heterodimer of X and Y") | U2, L-086 | RCSB search by UniProt accession, filtered by sequence coverage; state filters from the entry's ligand list or entity count. Freeze with the date. Grade with accepted ids plus the `exists` outcome (L-041) |
| S3 | Two-turn edit: turn 1 is any generated task's reference; turn 2 changes one thing ("colour it red", "hide the waters too", "make that a surface", "the rest grey") | U11, issue #5 | Apply the edit to the turn-1 reference with the same generator code. Final-state grading makes clobbering lose points. Include one "do nothing new" edit (ask to show what is already shown) |
| S4 | Named-atom contact: "draw the bond between the iron and the proximal histidine", "the H-bond between Ser195 and His57" | U4, ROADMAP R3 | Neighbour search with gemmi; keep pairs with exactly one candidate within the cut-off so the answer is unique; distance stored in provenance |
| S5 | Binding site or interface as an explicit residue list: "show the residues within 5 Å of the ligand as sticks" | U3, L-085, predecessor comp-001/005 | Neighbour search gives the residue set. The model must list residues because MVS has no distance term — closed-book this is very hard, so run it mainly in the grounding-pack condition, or give the residue list in turn 1 and test the edit. State this choice in the paper |
| S6 | Secondary-structure selection: "colour the helices blue", "hide the sheets", "colour the second helix yellow" | U5, predecessor sel-008/009 | Ranges from the entry's `_struct_conf` / `_struct_sheet_range` records, converted to residue ranges. The colour-by-secondary-structure *theme* is a separate, simpler template |
| S7 | Residue-property and position selections: charged residues, first 20 residues, backbone only, alpha carbons, all metal ions as spheres | predecessor sel-004/005/012/015, comp-008 | Residue names and atom names straight from the atom table; ions from the mmCIF chemical component types |
| S8 | Range specs: several (chain, start, end, colour, label) rows in one prompt; variant where numbers are UniProt positions on an entry with an offset | U6, D4 | The rows are the reference. The UniProt variant maps through frozen SIFTS and makes a tier-3 task from a real usage pattern |
| S9 | Look-alike ids: load an id one character from a famous one (1HH0 vs 1HHO) and apply a simple style | U15, L-106 | Reference is the typed id. Pairs chosen by script: edit distance 1 from a list of famous entries, both ids existing |
| S10 | Requests that should change nothing, in the follow-up tier: a question about the scene, or an operation the surface lacks (spin in MVS) | U10, U12, L-093 | Accepted final state = start state. Needs G5 settled |
| S11 | Variant by gene name: "show BRAF V600E" with or without the entry | U7, L-081 | UniProt position → frozen SIFTS → author residue on an entry chosen to have an offset; wild-type residue checked against the structure |
| S12 | Keep-only and negation: "everything except chain A", "hide all but the ligand", "water only between residue numbers m and n" | U13, issue #4 amb-006, predecessor sel-007 | Set complement on the atom table. In the API track the same intent is hide toggles plus a selection, a natural twin |
| S13 | Representation vocabulary: prompts that use another program's word (wireframe, licorice, trace, tube) | U14 | Small fixed synonym table mapping to the surface's representation types; accept set where two types are defensible. Skip words with no counterpart |
| S14 | Ambiguous one-liners: "clean up the view", "show me the drug", "focus on the important parts" | issue #4 | D7 accept sets: each reading generated by script from the entry's component types (waters, ions, ligands). Plus the no-own-goal floor (L-092) |
| S15 | Sequence motif: "colour the motif PA blue" | U6 | Find the motif in the entity sequence, map to observed residues through the atom table; skip when it occurs in unobserved residues |
| S16 | AlphaFold model by accession, API track | U16, L-004 | `custom_data` URL built from the accession, plus the confidence-colouring property |

Not seeded, with reason: assemblies and symmetry (U8) and superposition (U9) — out of scope for both
frozen surfaces (L-048, L-104); UniProt feature annotations (U17) — a live lookup (D9).

## (c) Contradictions between documents

- **C1. What the API track is for.** ROADMAP line 24 and PR #1 say it holds what MVS cannot express.
  The audits show 13 of 20 tasks are MVS-expressible and the viewer cannot do distance selection or
  arbitrary superposition. FINAL_PLAN D14 sides with the audits. ROADMAP still carries the old claim (the leaderboard
  copy was not checked).
- **C2. "API" means two things.** ROADMAP line 52 says MolBench is not "an API-calling benchmark"
  (meaning external lookups); the task folder is `tasks/api_calling` (meaning viewer calls). The
  paper should use "viewer API" for one and "lookups" for the other.
- **C3. Pilot key.** FINAL_PLAN phase C: "a tiny pilot on the direct Anthropic key". Memory:
  MolBench's own Anthropic key is out of credit; the key that works is the live chat site's, and
  the standing rule is not to run MolBench on it. An earlier note (2026-10-18) says Dan allowed it;
  the 2026-11-06 note withdraws that. Needs Dan's explicit OK or a small top-up of MolBench's key.
- **C4. Samples.** `paper/methods.md` says 3–5; the runner default and the October run are 1; the
  July API run used 3; FINAL_PLAN D12 says 3.
- **C5. Component 2.** ROADMAP calls it "the headline" and `paper/venues.md` calls it required for
  the top venue; FINAL_PLAN D8 puts it out of the paper. README line 46 and Methods line 12 still
  present it as part of the benchmark.
- **C6. Difficulty gradient.** `paper/venues.md` claim 1 says harder tiers separate models more.
  With 15 models that is false on the overall score and true only over valid scenes (L-078).
- **C7. Grounding packs.** ROADMAP calls spec + pack the "upper bound for an offline pipeline"; the
  measurement shows packs lower scores on average. The paper should present the result, not the
  expectation.
- **C8. Model counts.** ROADMAP header: 8 models. Memory index: 7. Leaderboard: 16 plus a baseline
  (15 on MVS). `paper/venues.md`: about 8.
- **C9. Task counts.** Issues #4 and #5 say 27 tasks; HANDOVER 84; `paper/venues.md` about 70;
  the repo has 90 graded plus 2 unrenderable.
- **C10. Escalation numbers.** ROADMAP Phase A: 285 escalated / 127 rescued. Live data after PR #16:
  294 / 84.
- **C11. "By construction".** Methods says no reference is hand-guessed. The 5 `tasks/mvs` tasks and
  all 20 API tasks are hand-written with no provenance, and six generated references were wrong
  until a human rater flagged them. D2 fixes the API side; the 5 hand-written MVS tasks need
  provenance and a structure test too, or removal.
- **C12. Thumbs.** ROADMAP R9 says "todo"; the site has had reactions since July (L-190).
- **C13. Backups.** The plan's audit list says raw runs are "now also in `~/Backups`"; that is the
  same machine. The audit's concern was off-machine loss.
- **C14. Venue path.** `paper/venues.md` recommends a fast L+M workshop paper; no edition after
  2024 was found. FINAL_PLAN D15 (preprint, then journal) replaces it.
- **C15. Engine-neutral.** `paper/venues.md` claim 3 and the README sell engine-neutral grading; the
  grader follows Mol\* 5.9.0 selection rules and only Mol\* renders MVS (L-173).
- **C16. Issue #5 vs D6 on clobbering.** The issue wants a clobber that happens to rebuild the right
  final scene "marked down". D6 grades the final state only, so such a rebuild scores full marks.
  D6 is the defensible choice (the viewer shows the same thing); close the issue with that reason.
