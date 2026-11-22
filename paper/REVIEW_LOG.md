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

## Round 2 (2026-11-22; first round of the third paper branch)

**Scores (clarity, of 10):** structural bioinformatician 7, machine-learning benchmark
reviewer 7, clinical geneticist 7, copy-editor 7, cold reader 7. The cold reader would accept
on clarity; the other four would not.

The five summaries "in my own words" were used as a test. All five were right on the design.
They differed on three points, and each was a place where the paper had not said the thing
plainly: what the model is given (only one summary said it), what the eight groups of task
are called (families, categories, tiers, types), and whose the earlier graders were.

### Must-fix items, all fixed

| Issue (raised by) | What changed |
|:---|:---|
| What the model is given was first said in Section 5.2 (machine-learning reviewer) | Abstract, a paragraph "What the model is given" in Section 1, Figure 1 (box 4 and caption), the structure-grounded bullet of Section 3.3 and Section 5.2 now say it: the request and a format guide, no structure file, no lookup, no picture. Section 5.2 also says what the system prompts tell the model about grading. |
| Clinical "Split A / Split B": an undefined 22, opposite polarity in Table 9, 59 against 48 in contribution 1 (four reviewers) | New Section 3.3.1 with a generated 2x2 table (new Table 2). The groupings are named by content, "copying the number" (primary) and "offset" (descriptive), with one polarity in the text, the table of results and Section 5.4. "Split" now means only public / held-back. Contribution 1 gives both 59 and 48. One traditional-name request is quoted in full. |
| Target score: what the target is, and where extra drawing stops costing (all five) | Section 4.2 says what the target is in each kind of task and that 64 tasks store none, and replaces "by its extent" and "far more than the target" with three rules (spill, extra on the target, unrequested context), the same as SI S4.3. The table of the running example has four new graded rows, one or two per rule; `corpus_values.py` asserts their verdicts. Box 1, Section 7 and SI S4.3 now agree that not every task stores a target. |
| Figure 1 showed "held-back split" where Section 3.7 lists "format rules" (three reviewers) | The fourth box is the format check; the held-back count moved into the corpus box; the control-set box says that the grader was developed against the set. |
| Figure 6: the third bar has its own denominator (three reviewers) | n is printed above every bar; the axis reads "Score (invalid answer = 0)"; caption and Table P2 say which answers the third series is computed on. |

### Should-fix and polish items, fixed

- **Words with two meanings.** *Model* is a language model only (predicted structure;
  first coordinate set; deposited coordinates). *Draw* is a verb only; the noun is *style*.
  *Panel* is the structure panel; the models are *core* and *optional models*. *Control*
  is the control set; a viewer is driven or operated. *Reference* is the reference answer;
  the prompt text is the *format guide* and the conditions are main, main + JSON mode,
  main + grounding pack, no format guide. *Tier* is *category*, because the groups are not
  ranks. *Pilot* is the October run; the small rating study is a *trial*. Valid, unshowable
  and schema-breaking replace seven words. Track, format and side are told apart in Box 1.
- **Box 1**: ClinVar (records, aggregate classification, review status), the variant
  notation, signal peptide, polymer, offset with its sign, F1 in two plain sentences, and
  ten terms that captions use (category, template, control, format guide, grounding pack,
  structure panel, core and optional models, keyword script).
- **Variant filter** (four reviewers, pulling two ways): three sentences in Section 3.1; the
  step table and every detail in new SI Section S3.2. It now says what a qualifying record
  is, that one such record is enough and that discordant records were not looked for, which
  protein-level name is matched, that the request uses ClinVar's own word, what the request
  of the lysozyme exception says, why the APOE variant is not asked, and what was read on
  which date. The unsourced statement about UniProt's rule is replaced by what we observed.
- **27 proteins, 25 with tasks, 31 structures**: stated as a sum from generated values
  (26 PDB entries and 5 predicted structures; two haemoglobin entries serve two proteins).
  How variants are picked from the pool is said.
- **Atom tables**: alternate conformers, hydrogens and insertion codes.
- **UniProt selector**: Section 3.4 says how the grader and the viewer each resolve it, that
  this path was not replayed in the viewer for PDB entries, and that the 13 traditional
  names must be converted on either track. Also a limit in Section 9.3.
- **Unrequested context** is stated in full once, in Section 4.2; Sections 3.4 and 3.5
  point to it.
- **Repetition**: Section 7 is a table (new Table 13) with no repeated numbers; "How Finding
  2 changed the design" is gone; Section 8 keeps two points; the 42% and 54% appear in the
  abstract, Section 4.5 and the conclusion only.
- **Control set**: the paragraph leads with what was confirmed in the viewers (890 of 1,110
  and 234 of 995) and lists what was not; the Table 4 caption gives the same counts.
- **Models**: Section 5.1 names the 16 core models and their price range, says which one was
  not in the pilot and which one has no JSON mode, and how optional models are decided.
- **Token limit**: 8,000, and 16,000 for reasoning and answer together for the 7 core models
  that reason first (main text and SI now agree).
- **Statistics**: models are fixed and structures resampled; an unshowable answer is not
  right in the paired comparison; valid-only pools a model's valid answers; 8 follow-up
  pairs have no target score.
- **Rating study**: Section 5.5 gives the sampling rule of the design note and what will be
  reported; Finding 6 opens with its purpose.
- **Held-back split**: Section 3.6 says how many public-split structures earlier tasks used
  (23 of 63) and what the split therefore compares; the disclaimers are in one place.
- **Promises without a table**: Table 8 has rows for name-resolution answers on the
  reference entry and on another accepted entry, a filled Structures column and valid-only
  columns for task success and target score (so Figure 5C plots numbers that a table holds);
  Table 10 has a difference row and rows for the matched tasks, and leads with the target
  score; the prediction under it is stated on the target score.
- **Figures**: in-figure titles dropped; Figure 3 states the majority rule; Figure 4 is
  "the reference and two answers"; Figure 5 captions say what a gap means.
- **Section 4.4** is headed and built on the three outcome classes; SI Table S4 has a class
  column. **Section 4.6**: camera, opacity tolerance, named shades.
- **SI S8**: the pilot tables are numbered S7 to S18 and shown in the paper's words. The
  build maps words only (`PILOT_WORDS` in `build.py`); the translation table is gone.
- **Smaller items**: Sections 9.1 to 9.4 numbered and cross-referenced; title of Section 11;
  citations at first mention in Section 2; the 20% statements; the review status explained
  where it first appears; Finding 1 (Pearson, unarchived text); Finding 5 (verb); Weights
  defined in both captions; "up to" in the row counts; the worked examples of the prompts.

### Declined, or done differently, and why

| Suggestion | Decision |
|:---|:---|
| Rename the held-back split to "new-structure split" (two reviewers) | Not done, because it would be wrong on the facts: 40 of the 63 public-split structures were also unused by earlier tasks. The task files and the plan call the split held-back. The paper now gives the counts and says that the held-back tasks are public. |
| Rating study: "half graded as success and half not" (two reviewers offered this as a guess) | The design note samples answers that the grader fails, half that the image judge calls the same and half different, plus 40 successes that are not pixel-identical. The paper states that rule. |
| "Chosen as low-cost models, at most $1.50 per million input tokens; none is a provider's largest model" | Not on record. The paper gives the generated range of list prices and calls them lower-priced. |
| "Nine core models reason; the limit is raised so that the visible answer still has 8,000" | The manifest flags 7 core models and gives 16,000 tokens for reasoning and answer together; the paper says that. |
| Print every model row in the per-model tables | The 16 names are in Section 5.1 and SI Table S6. Full rows would add some 300 pending cells to a draft. |
| Figure 5C as "share of answers that are target-right" | Kept as target score, which the analysis computes; the caption no longer calls the gap unrequested drawing, and Table 8 holds both valid-only numbers. |
| Resample structures of one protein together | The analysis resamples structures. The paper names this as a limit (Section 9.4). |
| An SI table that divides one-sided pairs by cause | Added to the list of what the final run must write (pending tag in Section 6.3); the paper says how to read the counts until then. |
| Keep the full statement on unrequested context in Section 3.4 (one reviewer; two asked for 4.2) | Section 4.2. |
| "Style group" for fact | "Fact" kept; "style" replaces "draw". |
| Glosses for SIFTS and ClinVar in the abstract | Short ones only; the abstract is at its 200-word limit. |

### Open, for the lead

1. **Final tables.** Shapes changed again: per-model table (columns), Table 8 (two answer
   rows under name resolution, Structures, two valid-only columns), Table 10 (groupings by
   name, difference row, matched-task rows, target score first), Table 12 (condition names).
   `scripts/paper_tables.py` must write `table_final_*.md` to match `generated/shape_*.md`.
2. **Helix and strand tasks in the clinical groupings.** `molbench/analysis.py` leaves the
   10 helix and strand tasks out of its clinical strata; the paper's counts (34 / 48, 23 /
   59) are of all 82. One of the two must follow the other.
3. **Pairs without a target.** 8 follow-up pairs have no target score. `target_solved`
   counts them as right on neither side. The paper says that they cannot be target-right and
   that Table 9a is read on the other 250; dropping them from that table would be cleaner.
4. **LYZ p.Ile74Thr.** Its request says "classified as pathogenic in ClinVar" although the
   record states no assertion criteria. The paper now names this as an exception (SI S3.2,
   Section 9.2). If the wording of the request changes, the sentence must follow.
5. **The scene format guide** has a short illustration of a distance line on 1A6M, a
   structure that 10 tasks use (none asks for that distance). The paper says so.
6. **Discordant ClinVar records** of the same amino-acid change were never looked for
   (step 2 needs one qualifying record). Stated in SI S3.2.
7. **Pepys et al. 1993** was added from its Crossref record. That it reports two variants
   (Ile56Thr and Asp67His) was written from memory: check at the source.
8. **Optional models**: a pending tag asks which of them are run.
9. Still open from round 1: the read-back record is older than the control set (80 scene
   controls not read back); the variant counts in CORPUS.md (43 / 37 / 246) differ from the
   generated ones (44 / 35 / 216); who the four reviews of the corpus were.
10. **Layout.** Four pages of the PDF were looked at (those with Figures 3, 5 and 6 and with
    Tables 6 and 13). Figures 1, 2 and 4 were not looked at in the PDF, and the rest of the
    layout was not checked.
