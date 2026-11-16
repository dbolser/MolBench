# Review log of the manuscript

Clarity reviews by five readers (structural bioinformatician, machine-learning benchmark
reviewer, clinical geneticist, copy-editor, cold reader). One entry per round: scores, what
changed, what was declined and why. Numbers in the paper still come only from
`paper/generated/` through `paper/corpus_values.py`, `paper/figures.py` and `paper/build.py`.

## Round 1 (2026-11-16)

**Scores (clarity, of 10):** structural bioinformatician 6, machine-learning benchmark
reviewer 6, clinical geneticist 6, copy-editor 6, cold reader 6. None would accept on clarity.

### Must-fix items, all fixed

| Issue (raised by) | What changed |
|:---|:---|
| The running example was "yellow spacefill" in the request and "green ball-and-stick" in Table 2, Figures 3 and 4, SI S1 and S4.3 (all five) | The strings were typed in `corpus_values.py` and `figures.py`. They now come from the task (`ex.color`, `ex.rep`, `ex.rep_short`, `ex.rep_scene`). `build.py` fails if the table or the two figures do not show the request's colour and representation, or name another representation (tried: a hand-broken table fails the build). |
| "75" in Section 4.3 (all five) | Left over from the earlier example; now `{{ex.uniprot_position}}` of `{{ex.name_in_prompt}}`. |
| The request was quoted in two forms (all five) | Section 1 quotes `{{ex.prompt}}`, as the figures and the SI do. Figure 3 no longer says "the model must know the accession". Sections 3.3 and 3.4 say that 46 of the 82 clinical requests state the accession and what that means on the call-list track. |
| Strict / valid / repaired defined three ways (four reviewers) | Section 4.4 separates "cannot be shown" (scores 0) from "breaks the call schema" (replayed, keeps its scores, not valid). Box 1, Tables 5 to 7 and SI Table S4 use the same words. Box 1 lists three ways to average. |
| Two or five AlphaFold models (four reviewers) | Five everywhere, from `panel.n_alphafold`; the proteins are named from the panel file (`panel.alphafold_proteins`) in Section 3.1 and SI S3. |
| Cross-reference to Section 5.3 for the paired comparison (two) | Section 5.4. |
| Over-claim on variant nomenclature (clinical geneticist) | Box 1 and Section 3.1 now say what was checked: the position is that of the UniProt canonical sequence, and a ClinVar variation record that UniProt cites must list the same change at that position. Transcripts were not compared, and the paper says so. Section 3.2 gives the full names of both ClinVar records of the running example, from the frozen records. |

### Should-fix and polish items, fixed

- **Variant filtering** (four reviewers): the paragraph is now a short step table (generated,
  `table_variants.md`) with one paragraph per step. The lysozyme exception is stated to be
  outside the 2,400, the APOE exclusion inside. Dates say what was read when. Figure 1 shows
  2,400. Missense, classification, haplotype and review status are explained.
- **27 proteins, 25 with tasks, 31 structures** (four): reconciled in Section 3.1 from new
  generated values.
- **59/23 against 48/34** (all five): Section 3.3 names the two splits (A and B) and derives
  34 = 22 + 12 from new generated counts. The reviewers guessed 23 + 11; the task files give
  22 + 12 (one traditional name sits on a predicted model, where it is wrong). Table 9 labels
  the splits.
- **Twenty tasks on two structures against "five plus three" sets** (clinical geneticist):
  10 sets of matched tasks, 8 with an offset contrast on 4 proteins, from generated values.
- **When must a call list hide the default view** (three): Section 3.4 states the rule and
  quotes one such request from the corpus.
- **Paired comparison** (all five): "target-right" (target score exactly 1) and the three
  levels of task success (per answer; task success rate; all-3; majority) are defined in
  Section 4.2. Table 8 is two tables, 8a by target score and 8b by task success. Figure 3 and
  Figure 5B say the same. The cells are named "right in scene only" and so on. Section 6.3
  says how clinical pairs must be read.
- **F1 = 0.40 not derived; "F1 alone cannot tell"** (four): Section 4.3 works the case through
  from generated values and replaces the wrong sentence. Figure 4 says "fact".
- **Target score: "wraps" and "passes through"** (three): replaced by the extent rule of SI
  S4.3, including that a whole-chain surface that would hide the target is ignored.
- **Unrequested context told in four places** (two): one paragraph in Section 4.2 states the
  rule for both tracks and which score ranks models; Section 3.5 is rewritten; Section 7
  points to Finding 2.
- **"Pair" used for four things** (three): kept for the defined term only. Controls are
  "controls", rating items "picture comparisons", clinical sets "matched tasks".
- **Synonyms** (copy-editor): drawn state (not final or end state), answer (not output, reply
  or sampled answer), valid-only, keyword script, unrequested context (not scenery), fact (not
  display class or display fact), accepted answer (not alternative, state or reading), main
  condition and primary score (not headline).
- **Lookup tiers** (four): defined in Section 3.3 and Box 1 as name resolution and clinical
  variant, which is what the run manifest and the figure shading mean.
- **"Tiers of difficulty"** (three): "grouped by what the model must know".
- **Held-back split** (four): the definition in Box 1, Section 3.6, Figure 1 and Section 9 now
  says in short sentences what it is and what it compares.
- **30 requests, 82 files** (two): 30 requests, 11 of them pairs, so 41 tasks and 82 files; one
  request is quoted in its three phrasings.
- **Control set** (three): the zero-error caveat now comes before Table 3; the abstract and
  contribution 2 no longer say "measured error rate"; Table 3 has its missing percentage.
- **890 + 140 is not 1,110** (two): see "Open" below; the paper now says what was read back.
- **Name resolution compared as text** (two): said in Sections 3.3 and 4.1, not only in the
  limitations.
- **Models** (four): Section 5.1 states the rule, the 15 + 1, and how optional models are
  decided. Table 4 has a samples column and names the three models.
- **Multiple comparisons** (one): reworded.
- **Colour tolerance** (three): the distance is defined.
- **Section 3.7** (three): denominators and the nature of the sample are given.
- **Finding 6** (four): split into what was done, result and limits; "rescue" dropped.
- **Section 6.6 heading** (one): says the answers are regraded with the present grader.
- **Limitations** (two): a lead sentence names the four that matter most; the rest are grouped
  under Scope, Corpus, Grader and Run. The widget detail moved to SI S4.8.
- **Conclusion** (cold reader): new Section 10; Ethics and Availability are Sections 11 and 12.
- **Related work** (two): opens with the gap; the note on checking moved to the end.
- **Box 1** (three): a first block of background terms; file item names for the numberings;
  entry, offset, target, answer and unrequested context defined.
- **Abstract** (three): SIFTS named; the control-set and pilot sentences reworded; 200 words.
- **Figures** (several): Figure 1 labels use the paper's words; Figure 5A no longer says 17
  rows; Figure 6 legend says drawn state and the caption explains the pooled tiers.
- **Result tables** (one): Tables 5 and 8 show their first rows in the draft.
- **Project-internal names** (copy-editor): removed from Section 12, SI S6 and SI S7. The
  ">>" in the printed scene prompt was an artefact of the SI script and is gone.
- **Smaller items**: Table 10 and 11 captions, the atom limit in Section 9, "the residue it
  replaces", I56T and W64R, 14 heavy atoms and 10 hydrogens, the patient-data sentence, title
  case, pending tags for the table-of-contents graphic and author information.

### Declined, or done differently, and why

| Suggestion | Decision |
|:---|:---|
| Drop "computational intelligence (CI)" and its Box 1 row (four reviewers) | Done as asked, and it stays within the house rule: the paper never says "AI". It says "language model" throughout, so the abbreviation CI, which readers of a statistics section take for "confidence interval", is not needed. If the author wants the term visible, the place is the single sentence in Section 9 about the coding assistant. |
| Rename the held-back split to "new-structure split" (three reviewers) | Name kept. The task files, the tables written by the analysis scripts and FINAL_PLAN decision 21 call it the held-back split, and two reviewers offered a sharper definition as the alternative. The definition is now explicit that the split is public. |
| Number the variant steps as a table and renumber | The step table is unnumbered, inside Section 3.1, so that Tables 1 to 12 keep their numbers. |
| Move SI Table S4 into the main text (one reviewer) | The two terms it rests on are now defined in Section 4.4; the table stays in the SI to keep Section 4 short. |
| Regenerate the SI S8 pilot tables with the paper's terms (copy-editor) | Not possible from here: those tables are written by `scripts/paper_tables.py`, which this job may not change. S8 now has a two-column key from the old words to the paper's. |
| "Mean over the 16 core models" in every caption (copy-editor) | Captions say "mean over the models of the panel (the keyword script is left out)", which is what the analysis code documents. Whether optional models enter the mean is not stated there; see Open. |
| Reviewers' arithmetic "23 + 11" | The corpus gives 22 + 12; the paper uses the generated counts. |
| Add RefSeq accession to the nomenclature rule (clinical geneticist) | The pipeline does not test transcript identity, so the paper does not claim it; it states what is tested and quotes the ClinVar record names, which carry the transcript. |

### Open, for the lead

1. **Read-back record is older than the control set.** `tests/controls/viewer_check.json`
   was written on an earlier control set (1,030 scene controls: 890 read back, 140 not
   readable). The set now has 1,110. The paper says that 80 scene controls added since have
   not been read back. Re-running the read-back would remove the sentence.
2. **Counts in the audit table of CORPUS.md differ from the generated ones.** CORPUS.md and
   `data/corpus/corpus_notes.md` give 43 / 37 / 246 for other-gene, haplotype and no-criteria
   variants; `molbench.variants` gives 44 / 35 / 216, which the paper uses. Not chased.
3. **Final tables.** The shapes in the paper changed: Table 8 is 8a and 8b; Table 9 names
   Split A and B; Tables 5 and 8 are shortened in the draft. `scripts/paper_tables.py` must
   write `table_final_*.md` in these shapes and with the paper's column names.
4. **Abstract length.** It is at the 200-word limit. The two result sentences must replace
   the two sentences on the pilot run; the PENDING tag says so.
5. **Who the four reviews of the corpus were.** Section 7 says language-model reviewers with
   four roles, from the audit record. Confirm the wording.
6. **Means over models** in Tables 7 and 9 to 11: state whether optional models are included.
