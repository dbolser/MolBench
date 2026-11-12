# Final benchmark plan (2026-11-12)

Goal: a publication-ready benchmark and paper draft, built at $0, followed by **one** paid
model run that fills every results table. Nothing below needs OpenRouter until step "Final run".
This file is the shared brief for everyone working on the `final-benchmark` branch. The evidence
behind it is the 2026-11-06 audit (summarised in "Audit findings" at the bottom).

## The paper in one paragraph

MolBench measures whether a language model can turn a plain-language request into correct control
of a molecular viewer. Every reference answer is built by script from the deposited structure
(never hand-guessed), and every answer is graded by **what the viewer would show**: the atoms
selected, and how they are drawn and coloured. The same requests are posed in two output formats —
a declarative scene (MolViewSpec, MVS) and an imperative call list (PDBe Mol\* viewer API) — so
that "does not know the biology" can be separated from "cannot write the format". Difficulty rises
from translation, to structure-grounded, to clinical-variant requests that need a UniProt →
structure residue mapping.

## Decisions (made; change only with evidence)

1. **Two tracks, one grading idea.** MVS track (headline) and API track. Both graded on resolved
   atom sets / final viewer state. Headline metric per task: F1 (graded) plus **task success**
   (final state exactly right). Report both everywhere.
2. **API track is rebuilt, not just enlarged.** New state-replay grader (`molbench/pdbe_state.py`)
   that follows pdbe-molstar 3.3.2 semantics; no pooling of author and label numbering or chain
   ids. All 20 hand-written tasks are fixed or replaced, each gets provenance and a
   reference-vs-structure test. Then ~130 generated tasks (total ≈ 150).
3. **Paired tasks.** Every MVS task that the API can express gets an API twin with the same prompt
   and the same target atoms. Reported as a separate paired analysis (McNemar on task success).
   Clinical twins are flagged: the PDBe viewer resolves UniProt numbering itself, MVS cannot.
4. **Clinical tier is widened.** From 9 tasks on 1TUP (where UniProt = author numbering) to ≥ 40
   tasks on ≥ 12 proteins, at least 8 of them with a UniProt ≠ author offset. Frozen SIFTS tables;
   no network at grade time.
5. **Structure diversity.** ≥ 50 PDB entries overall (now 14). Atom tables + frozen SIFTS +
   grounding facts for each. Confidence intervals are clustered by structure and template.
6. **Follow-up turns (issue #5): in.** ~30 two-turn tasks (start scene + edit request), both
   tracks, graded on final state so clobbering earlier choices loses points.
7. **Ambiguous prompts (issue #4): small accept-set tier** (~15 tasks, several accepted final
   states, built by script). No rubric judge.
8. **Component 2 (open-ended, rubric VLM judge): out of this paper.** Stated as future work. The
   image-pair VLM judge stays as a side column, validated by the human rating study (A4).
9. **No live tool loop, no agentic track.** The roadmap trigger (grounding lift ≥ 10 F1 points) was
   tested and not met. Grounding packs stay as an ablation on the lookup tiers.
10. **Prompt conditions in the final run:** `spec` (headline, all models); `spec + grounding pack`
    (lookup tiers only); `bare` (3 models, one line in the paper). No prompt tuning on test tasks.
    The API prompt's worked example must not be a benchmark task.
11. **Output validity is reported, not hidden.** Strict score (invalid output = 0) is primary. Also
    reported: score over valid outputs only, and the offline `json-repair` counterfactual (free).
    A structured-output (JSON mode) condition is run for models that support it.
12. **Samples: 3 per task per model**, temperature as provider default, every raw output archived.
13. **Reproducibility:** one manifest file names the corpus version, models, conditions, samples
    and prices. One command does the run; one command rebuilds every table and figure in the paper
    from the archives. A dry run with a mock model exercises the whole path at $0.
14. **Viewer target stays pdbe-molstar 3.3.2** (what ipymolstar 0.1.0 loads). The roadmap line
    saying the API track covers distance selection / arbitrary superposition is wrong and is
    removed. Mol\* v6 command layer = future work.
15. **Venue:** preprint first, then JCIM or Digital Discovery. Paper lives in `paper/` as Markdown
    with every number injected by `scripts/paper_tables.py`. Numbers awaiting the final run are
    written as `⟦PENDING: what⟧` so they are easy to find.
17. **A reference holds only what the request states** (found 2026-11-12: clinical references drew
    an unrequested grey cartoon, and that — not the residue lookup — is where models lost points:
    85 of 96 valid clinical scenes had the residue exactly right, 2 scored 1). If context is wanted,
    the request asks for it in words. Every task also reports a **target score**: the requested
    atoms alone (selection, representation, colour).
18. **"Exactly right" is defined on what is drawn.** Task success compares, per atom, the set of
    representations and the colour. Harmless namings are equal (`all` vs `polymer` under a cartoon;
    a chain-id colour theme vs the same colours per chain). Unrequested extra drawing fails success
    and costs precision. Each case is pinned by a test, and a **grader control set** (identical
    pairs, equivalent pairs that must pass, wrong pairs that must fail) gives the grader's own
    error rate for the paper.
19. **"No change" is a valid answer.** Follow-up tasks always return the full scene / full call
    list, so "nothing to do" is the start state returned unchanged. A few such tasks are included.
20. **Paraphrases.** ~30 tasks get 3 scripted phrasings each (full, terse, indirect) to measure
    sensitivity to wording. Real user phrasings from the chat site seed the terse forms.
21. **Contamination.** Tasks have been public since May 2026; the paper says so. Generators are
    seeded, and a **held-back split** (same generators, different structures, never published
    before the run) is run alongside and compared with the public split.
22. **Model panel by rule:** the open and closed models already tracked, plus current frontier
    models from each major lab as optional entries; the rule is written in the manifest. The
    keyword baseline is a panel member on both tracks.
23. **Human rating study v2 validates the headline metric,** not only the image judge: people see
    reference and answer renders, framed on the target atoms, and say same / different; that is
    compared with the grader's task success and with the image judge. v1 is reported as a pilot.
24. **Renders are framed on the target** (same camera for reference and answer), because raters
    could not see one-residue targets in whole-molecule views.
16. Vocabulary: "computational intelligence (CI)" not "AI", per Dan. Plain scientific language.

## Phases

- **A — foundations** (parallel): structure panel + data layer · API state grader + reference
  fixes · runner/manifest/dry-run · paper tables from October data + skeleton + related work ·
  rating-study readout · ledger of every TODO and idea in both repos with a disposition.
- **B — corpus**: MVS generators on the new panel (tiers 1–3, interactions, resolve), API
  generator + twins, follow-up turns, accept-set tier. Freeze as `corpus-v1.0`.
- **C — proof**: $0 dry run of the full manifest; a tiny pilot on the direct Anthropic key
  (≈ $1) to prove parsing and grading end to end; complete paper draft; clarity review panel until
  10/10; rating set v2 + "final call" note for the human raters.
- **Final run** (paid, Dan's go): one command.

## Rules for everyone on this branch

- **No paid model calls.** No OpenRouter. Free public data downloads (RCSB, PDBe, UniProt,
  AlphaFold DB) are fine and expected; cache what you fetch into the repo's frozen data.
- References are built by script and tested against the structure. Never hand-guess.
- Never pass `--no-archive`. Never print or commit `results/a4/a4-v1/key.json` or any key.
- Work only in your own worktree and only in the files you own; report cross-cutting needs
  instead of editing someone else's file. Commit on your branch; do not push or open PRs.
- `uv` for Python (`uv sync`, `uv run pytest -q`). Tests must pass before you finish.
- Report honestly: what you built, what you verified and how, what you could not verify.

## Audit findings (2026-11-06) this plan answers

- No paper yet: `paper/methods.md` is a stale 1,500-word sketch (says 3–5 samples; runs used 1).
- API track: a keyword script scores 0.715 vs 0.72–0.95 for models; api-002 is the prompt's worked
  example; api-008/019 use label numbering for author residues; api-016 cannot run as written;
  grader pools author/label numbering and chain ids, ignores order and `keep_colors`, ignores
  `uniprot_*`; API tasks store `skills` but the runner reads `categories`.
- Clinical tier: 9 tasks, one protein, no numbering offset.
- Only 14 PDB entries; 1 sample per task; no confidence intervals.
- Valid-scene rate explains MVS F1 almost entirely (r = 0.996 over 15 models).
- CI runs 2 of the test files and installs with pip.
- `scripts/build_site_data.py` has hard-coded dates and task counts.
- Raw runs and the rating-study key exist only on one machine (now also in `~/Backups`).
