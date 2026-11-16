# MOCK tables: final shapes, fake numbers

> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

Nothing here may be quoted as a result. The real tables are written to another directory and never mixed with these.

Built by `scripts/paper_tables.py --from-dry-run` from the scorecards in `results/final-v1.dryrun`
(run `final-v1`, corpus `corpus-v1.0-dev ef851e529f43`, 67 scorecards). Rebuild, do not edit.

| file | what |
|---|---|
| `table_corpus.md` | Corpus: original tasks by tier, track and split |
| `table_corpus_kinds.md` | Corpus: special kinds of task (original tasks) |
| `table_corpus_difficulty.md` | Corpus: difficulty facts under one vocabulary |
| `table_panel.md` | Model panel |
| `table_controls.md` | Grader control set: the grader's own error rate |
| `table_mvs_leaderboard.md` | MVS track: leaderboard (378 original tasks, headline condition, 3 samples per task) |
| `table_mvs_validity.md` | MVS track: what came back (samples, headline condition) |
| `table_mvs_tiers.md` | MVS track: task success by tier [95% CI] |
| `table_api_leaderboard.md` | API track: leaderboard (403 original tasks, headline condition, 3 samples per task) |
| `table_api_validity.md` | API track: what came back (samples, headline condition) |
| `table_api_tiers.md` | API track: task success by tier [95% CI] |
| `table_tier_track.md` | Tier by track: panel mean |
| `table_tracks.md` | The two tracks, model by model |
| `table_mvs_split.md` | MVS track: public and held-back tasks (task success) |
| `table_api_split.md` | API track: public and held-back tasks (task success) |
| `table_mvs_paraphrase.md` | MVS track: sensitivity to wording (24 requests, three phrasings each) |
| `table_api_paraphrase.md` | API track: sensitivity to wording (20 requests, three phrasings each) |
| `table_paired.md` | The same request in both formats: paired analysis |
| `table_followup.md` | Follow-up turns: the edit made, and what had to stay |
| `table_followup_edits.md` | Follow-up turns by kind of edit (panel mean) |
| `table_accept_readings.md` | Accept-set tier: which reading the right answers took |
| `table_accept_tasks.md` | Accept-set tier: right samples per reading (supplement) |
| `table_clinical_strata.md` | Clinical tier: results by what the task demands (panel mean) |
| `table_clinical_models.md` | Clinical tier: task success when the number in the variant name is already the author number, and when a mapping is needed |
| `table_clinical_pairs.md` | Clinical tier: the same variant on two structures (panel mean task success) |
| `table_difficulty.md` | Task success by difficulty fact (panel mean, all tiers) |
| `table_resolve_entries.md` | Resolve tier: which entry the answer loads (share of samples) |
| `table_structured.md` | Structured output (the provider's JSON mode) against plain output |
| `table_grounding.md` | Grounding pack against none, on the lookup tiers |
| `table_bare.md` | Bare prompt (output contract only) against the prompt with the reference |
| `table_cost.md` | Calls, tokens and cost of the run |
| `values.json` | every number above as a flat key → value map; `"status"` says whether it is mock |
