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

## Round 3 (2026-11-23; second round of the third paper branch)

**Scores (clarity, of 10):** structural bioinformatician 8, machine-learning benchmark
reviewer 8, clinical geneticist 7, copy-editor 8, cold reader 7.5. All five would accept on
clarity.

### Must-fix items, all fixed

| Issue (raised by) | What changed |
|:---|:---|
| The primary paired comparison had two denominators: 258 in Table 9a, its caption and Figures 3 and 5B, 250 in Section 5.4 (four reviewers) | Table 9a, its caption, both figures and Section 5.4 now say the same: the primary comparison is on the 250 pairs that have a target score, and the 8 follow-up pairs without one appear in Table 9b only. The numbers are `corpus.twins.n_with_target` and `n_without_target`. Section 5.4 also says that none of the 8 is among the 15 pairs whose call list must hide the default view (asserted by `corpus_values.py`). |
| "Most answers drew the right residue" over-claimed by omission; the Conclusion contradicted Finding 1 (clinical geneticist) | Abstract, Section 6.6 (Finding 2), Section 8 and Section 10 now say that the single pilot structure needed no renumbering, so the statement is about drawing and not about mapping. The Conclusion says that the reference flaw was the largest loss in the clinical category, and unshowable answers over the whole pilot. |

### Should-fix and polish items, fixed

- **Variant filter** (four reviewers): Section 3.1 names the candidates (3,352) and the two
  steps with their counts (657, 295) in words; the two hand-made exceptions (lysozyme
  p.Ile74Thr, one *APOE* variant) are in the main text; "germline" is in Box 1 and Section 3.1.
- **The 27 proteins** were chosen by hand, and the paper says so (Section 3.1, SI S3.1). The
  two proteins without a task are named with the reason for each (no variant left; the one
  left is not observed in the structure), asserted by `corpus_values.py`. The paragraph on the
  pool was cut from eleven counts to the three that matter.
- **Multi-variant and helix tasks in the two clinical groupings** (three reviewers): the rule
  is stated (copying is right only if right for every variant; offset if any target residue
  has one; a helix task takes the properties of the variant's residue), with the fact that all
  8 multi-variant and all 10 helix or strand tasks sit in "offset, copying wrong" (asserted).
- **Variant notation** (clinical geneticist): Section 3.3.1 states the three forms of name and
  that "p." marks UniProt numbering; HGVS is named and cited (den Dunnen et al. 2016, checked
  at Crossref); ClinVar's own transcript-level name of the running example is quoted; the
  paper writes p.W82R wherever the UniProt-numbered name is meant; gene symbols are italic.
  The 36 requests without an accession are discussed. R136L is given as p.Arg154Leu.
- **ClinVar caveats** (clinical geneticist): Section 9.2 now says that transcripts were not
  compared and that discordant records were not looked for. The running example's records are
  identified in Section 3.2, with the "not provided" condition field. Box 1 corrects "one
  change at the level of DNA".
- **Target score** (three reviewers): rule 1 says that spill is judged on the style the answer
  drew on the target in the requested representation, whatever its colour (checked in
  `molbench/drawn.py`); a paragraph after rule 3 gives the reason for the line between rules 2
  and 3 and names its cost, with the two rows of Table 3. "766 of 797 tasks have a target
  score" replaces the sum the reader had to do.
- **F1** (three reviewers): the definition comes first; a cartoon as a style of atoms is
  explained; the call-list rule has three cases, a reason and the example of Table 3.
- **Table 3**: rows are numbered S1 to S10 and C1 to C5 and cited by number through generated
  keys (`ex.row.*`); the caption derives the two spill rows (24/56 and 24/2,691) and says what
  the default cartoon costs on each track; the Answer column is wide.
- **Planned comparisons** (two reviewers): seven are listed and numbered; 1 to 6 are the rows
  of Table 12 (numbered), 7 is the difference row of Table 10.
- **Format guide** (structural bioinformatician): Section 5.2 says what each guide contains,
  how long it is (975 and 1,211 words; system prompts 1,216 and 1,514 words) and that neither
  says which numbering an entry uses. SI S7 prints both guides in full, with a glossary of the
  words the prompts use. Lengths are in words because no tokenizer is used.
- **Other facts added**: which file the atom tables come from, and that the call-list
  viewer's own copy of a file was not compared (Sections 3.1, 3.7, 9.3, SI S4.8); how the list
  of accepted entries for name resolution was made (Section 3.3, SI S4.4) and that all three
  scores on an entry outside the panel come from the text comparison; why the call-list
  controls use 74 structures (Table 4, SI S5); why the grounding pack is run on the scene
  track only; that the three answers of a task are not resampled; which models run in JSON
  mode; what an informative result of the held-back split would be.
- **Terms**: Box 1 is split in two. Box 1 (Section 1) holds background and corpus terms and
  names the seven terms that carry the results; Box 2 (start of Section 4) holds grading and
  run terms. New entries: default view, component, accepted answer, copying the number,
  all-3 rate and majority, invalid, task, insertion code. Alternate conformers and the jargon
  of Section 9.3 are explained in place. "Open / closed weights" is the only pair of terms for
  that property; "rejected" replaces "failed" for the grader; "phrasings" replaces
  "paraphrases"; "full wording" is introduced; "about the same variant".
- **Abstract** (four reviewers): states the thesis (by rule, no judge model) and the question
  (convert or copy); no sentence begins with a numeral; "16 core models and up to 5 larger
  ones"; "each task"; the call-list viewer's own conversion is named. It is at its 200-word
  limit.
- **Introduction**: the paragraph on the running example opens with the wrong picture and
  then explains the two ways of counting; contribution 1 gives one count (48).
- **Call-outs**: every table and figure is cited in the text, in order of first citation.
  The two pilot tables are Tables 13 and 14, "what changed" is Table 15, licences Table 16.
  "Section 7 (rows 1 and 2)" is "Table 15".
- **Figures**: all schematics are redrawn at 660 px, the width at which they print, and
  `figures.py` refuses in-figure text below 9.5 px (7 pt). Figure 1 has two rows of three
  steps; Figure 2 is a 2 x 4 grid, with the lookup categories framed in blue and tagged;
  Figure 4 has three strips with no empty band and the title "number copied from the variant
  name"; Figure 5A has one panel per track and its caption forbids the comparison; Figure 5C
  says why it is valid-only; Figure 6 prints shares as percentages, with an axis that says so.
- **Tables**: column widths are set in the generators; Table 8 has a header row per track
  and indented sub-rows; pilot tables use "task success rate", two decimals for F1 and
  "1,050"; Table 15 has a header for its first column; tables are not broken across pages
  where they fit on one.
- **SI**: S4.3 says what spill is judged on and why rules 2 and 3 differ; S4.8 is rewritten
  for coordinate sets and lone ions (8 tasks; checked with the grader on four of them); S8
  uses "Requested part", "Score of 1" and "Earlier-grader F1", so that no word of the paper
  has a second meaning there; Table S6 has a provider column.

### Corrected although no reviewer asked

- **The viewer replay of the call-list controls counted call lists, not controls.** The paper
  said that 234 of the 995 call-list controls were confirmed in the viewer. The record
  (`tests/controls/viewer_check.json`, `scripts/grader_controls.py`) counts 234 call lists,
  two per control, from a sample of controls. Sections 3.7 and 4.5, Table 4 and SI S5 now say
  that; the value `controls.viewer.api.n_not_replayed` is gone. How many controls were in the
  sample is not on record.

### Declined, or done differently, and why

| Suggestion | Decision |
|:---|:---|
| "The read-back confirmed that selections agree atom for atom on both" the archive file and PDBe's updated file (structural bioinformatician) | Not true as far as the record goes: the replay loaded the archive file into both viewers. The paper says which file was used and names the missing comparison as a limit. |
| Format guide lengths in tokens | Given in words: token counts differ by model and the build uses no tokenizer. |
| "Sixteen core models" spelled out in the abstract | The number is written by script; the sentence was recast so that no numeral starts it. |
| Keep the earlier graders' 42% and 10% in the abstract | Dropped from the abstract to stay within 200 words after the thesis, the question and the pilot caveat went in; both numbers stay in Sections 4.5, 7 and 10. The sentence "Tasks, graders and answers are open" went for the same reason (Section 12 says it). |
| Figure 3 caption: keep the sentence on traditional names with more context | Deleted from the caption, as the reviewer's second option; Section 3.4 says it. |
| A call-list row "default cartoon left in place" in Table 3 | That answer is the reference (row C1), which now says so; the caption states the contrast with row S5. |
| "Mendelian disease", "with crystal structures" for the 27 proteins | "Inherited disease" and "experimental structures": not every entry is a crystal structure, and the paper makes no claim about the mode of inheritance. |
| The reason why a protein with one variant gets no task: "a category needs a choice of variants" | Not the reason. The real ones are stated: no variant left, or the one left is not observed in the structure. |
| Why the grounding pack is not run on the call-list track: "if the reason is cost, say that" | The plan gives no reason. The paper states the two facts that make the condition less informative there and claims no motive. |

### Open, for the lead

1. **Table 9a on 250 pairs.** The paper now specifies it. `molbench/analysis.py`
   (`target_solved`) still counts the 8 pairs without a target score as right on neither
   side; the writer of `table_final_paired.md` must leave them out of Table 9a.
2. **Final table shapes changed again**: Table 8 (a header row per track, indented sub-rows),
   Table 9 (titles, Pairs column), Table 12 (a first column with the comparison number),
   Tables 13 and 14 are the pilot tables. See `generated/shape_*.md`.
3. **Call-list controls replayed in the viewer**: the number of controls in the sample is not
   recorded, only the number of call lists (234). A rerun of `grader_controls.py --viewer-api`
   could record it.
4. **PDBe's own copy of a structure file** was never compared with the archive file that the
   atom tables are built from. The paper names this as a limit.
5. **Lone ions** (8 tasks): ball-and-stick for a single ion scores a target score of 0. The
   paper states it as a limit; a grader rule could accept it.
6. **The 27 proteins "cause inherited disease"**: written from the panel's disease notes; one
   of them (TP53) also lists somatic cancers. Check the wording.
7. The main checkout of `final-benchmark` has uncommitted changes to `paper/corpus_values.py`
   and generated files; this branch changes the same script (new values, table shapes), so
   the merge will need care. Corpus numbers that moved on `final-benchmark` were not chased.
8. Still open from earlier rounds: helix and strand tasks in the clinical strata of the
   analysis; LYZ p.Ile74Thr request wording; Pepys et al. 1993 (two variants) to be checked at
   the source; which optional models are run; the 80 scene controls added after the read-back.
9. **Layout.** Looked at in the PDF this round: pages 4, 9, 10, 13, 18, 19, 25, 26 and 27 of
   41 (Box 1, Figures 2 to 5, Tables 1, 3, 6, 8 and the caption of Table 9). Figures 1 and 6
   were looked at as rendered SVG files, not on their PDF pages. Not looked at: the rest of
   the paper and the SI (51 pages), including how the printed format guides break across
   pages. Tables that do not fit under their caption move to the next page and leave white
   space (pages 18 and 26).

## Round 4 (2026-11-23; third round of the third paper branch)

**Scores (clarity, of 10):** structural bioinformatician 8, machine-learning benchmark
reviewer 8, clinical geneticist 7, copy-editor 8, cold reader 8. All five would accept on
clarity. All five summaries state the thesis, the three scores, the two formats and the
question correctly; none says how many models are run, and all say "convert or copy".

### Must-fix items, both fixed (clinical geneticist)

| Issue | What changed |
|:---|:---|
| Section 3.4 said that with a traditional name "the model must convert it on either track"; Table 2 says copying is right in 12 of the 13 | Section 3.4 now says what each case demands: the UniProt selector gives the wrong residue if the printed number is passed on; in 12 of the 13 the printed number is the author number, so selecting by author number is right on either track; in the one on a predicted structure the number must be converted. It also says how the call-list reference is written (the selector with the converted position; checked in the task files). |
| "The other 36 requests ... are still positions in the UniProt canonical sequence" | False for 6 of them. The script now counts 30 names with "p." and 6 traditional names among the 36 (`clin.n_no_accession_uniprot`, `clin.n_no_accession_traditional`), and the sentence says so. |

### Should-fix and polish items, fixed

- **Abstract** (all five). Rewritten in plain sentences: what SIFTS, ClinVar and UniProt
  supply; "pathogenic or likely pathogenic"; "usually by its UniProt sequence position"; the
  two formats as a list, with "which can convert the number itself" attached to the viewer;
  the two faults of the pilot as "The fault was ours: ..."; "a second score" in place of the
  undefined "target score". To stay within 200 words the sentence on the number of models
  went (it used the undefined "core models"); the PENDING tag asks the final abstract to give
  it.
- **Table 3 caption: "one division"** (three). The caption carries the sum through: 24/56 =
  0.43, 24/2,691 = 0.009, recall 1, harmonic mean 0.60 and 0.02, all from generated values.
- **Target score** (four). Section 4.2 gives target recall and target precision in words, so
  that Table 3 can be checked without the SI; the spill rule is one plain sentence; the text
  says why a follow-up turn that takes something away has no target score, and Box 1 no longer
  says that every task stores a target.
- **Call-list F1** (four). Rewritten without "a change is not a set of styles"; the text now
  says that any change to the right atoms earns one half there, that the scene rule gives 0
  for a wrong representation (checked with the grader: 0.0 against 0.5), and that F1 is
  therefore never compared between the tracks. Section 9.3 repeats it as a limit.
- **Viewer settings as facts and targets** (ML reviewer). Section 4.1, Box 2 and Box 1.
- **The 15 pairs and the 8 pairs** (structural bioinformatician). Both descriptions were
  loose. From the task files: the reference call list switches off part of the default view
  in 15 pairs, all first requests; the request asks for it in 9, and in the other 6 (whole
  protein as surface or spheres) the list without the call is accepted as well. The 8 pairs
  without a target score are follow-up turns: hide the water (2), set the background (2), no
  change needed (4). Sections 3.4, 5.4 and the caption of Table 9 say this; the script asserts
  that the two sets do not overlap.
- **Follow-up turns that need no change** (two). Explained with a request from the corpus;
  the two scene tasks that ask for a spin are named.
- **Clinical category** (clinical geneticist): the mature protein defined for all three cases
  (initiator methionine 7, signal peptide 4, signal peptide and propeptide 2 of the 13
  traditional names); HGVS reference sequences and why a UniProt accession is not one;
  transcripts explained with the running example; review status defined as level of review,
  with counts for the 87 variants (15 single submitter, 52 several submitters, 19 expert
  panel or practice guideline, 1 without criteria); what "in every chain that has it" means
  (21 requests, 14 name one chain); the sign of the offset; the three wordings; the 2 matched
  sets of p53; the 9 proteins with a well-known variant tried first and their list in the SI;
  ClinVar classifies DNA changes (Introduction).
- **ClinVar was not searched** (clinical geneticist). Sections 3.1, 7 and 9.2 and SI S3.2 say
  that only the records that UniProt cross-references were examined.
- **One numbering for the variant filter** (two). Steps 1, 2, 3 in the paper and the SI, with
  the three counts of step 3 in the paper. SI Table S3b is Table S4; the later SI tables moved
  up by one (S4 to S19).
- **25 proteins, 26 PDB entries** (structural bioinformatician). Section 3.1 says how a
  protein comes to have tasks on more than one structure (6 proteins).
- **Sample of call-list controls replayed in the viewer** (three). See "Corrected" below.
- **Section 4 opened with a signpost** (cold reader). It opens with what the grader does and
  the three scores.
- **Whose calls** (copy-editor). Section 3.4: a JSON notation of our own, one item per call or
  setting of PDBe Mol\* 3.3.2, under the names of the notebook widget ipymolstar 0.1.0.
- **A scene whose file cannot be loaded** (copy-editor). Section 4.4 and SI Table S5: it is
  unshowable and scores 0; a scene on a readable but unaccepted entry is valid and scores 0.
- **Table 10 and the fourth pattern** (structural bioinformatician). Section 6.4 lists four
  patterns, among them the model that always converts. The Question in Section 1 defines
  mapping as giving the number that the structure uses.
- **Pilot section**: Finding 1 gives the correlation with the strict task success rate as
  well (r = 0.93) and names the columns; Finding 3 says that every pilot task had a grounding
  pack; Finding 6 is one paragraph, with the full account in SI Section S8.1; the earlier
  scene grader's 3% of false passes is in the text and in Table 15.
- **SI**: Section S0 (background terms, moved from Box 1, with het group, C-alpha, helix and
  strand added); Section S8 says in which direction its numbers differ from Section 6.6, why
  85 and 87, and that one class of Table S10 is empty; plain column heads in Table S18;
  Section S9 for the final-run tables.
- **Limitations**: the clinical bullet is three bullets; the two limits of the paired
  comparison (the viewer maps on one track; the prompts differ in length) are in Section 9.4.
- **Figures**: Figure 2 gives 48 of 82 (copying is wrong), not 59; Figures 3 and 5 use the
  cell names of Table 9; the example marks of Figure 5 have the final colours and shapes,
  drawn pale; Figure 1 says "averages: strict, valid-only". Captions of Figures 2 and 5 and
  of Tables 4, 9a, 9b, 10 and 12 follow the reviewers.
- **Lists and long bullets**: core models by weights with the developer of each; name
  resolution bullet; the statistics bullets on intervals and on the paired comparison in
  labelled parts; atom tables (detail to SI S3.1); proteins without a task (to SI S3.2).
- **Style** (copy-editor): dates as "13 November 2026" (`{{key:date}}`), small counts in prose
  as words where a reviewer pointed at them (`{{key:word}}`), "Data and Software
  Availability", "Errors in the first version and their corrections".

### Corrected although no reviewer asked

- **How many controls were replayed in the call-list viewer.** The record holds only the
  number of call lists (234). The check takes controls in a fixed order, one from each kind in
  turn, up to a number given on the command line. Applied to the control set that was
  committed with the record (850 call-list controls), that order gives 234 replayed and 3
  not runnable lists for exactly one sample size: 120 controls, of whose 240 lists 3 select
  by UniProt number. `paper/corpus_values.py --viewer-sample` does this from the git history
  and writes `generated/viewer_sample.json`; the build stops if the file does not fit the
  record. The paper now says 120 of 850 (14%), and that 145 call-list controls were added
  afterwards. Round 3 had "234 of the 995", then "a sample".
- **The 15 pairs "that must switch off part of the default view".** In 6 of them the call is
  not required (see above).
- **The target score of follow-up turns.** The text said that the tasks without one "take
  something away or reset a setting"; some of them need no change. Reworded.

### Declined, or done differently, and why

| Suggestion | Decision |
|:---|:---|
| Rename the held-back split "new-structure split" (structural bioinformatician) | The name would be wrong on the facts: the public split also contains structures that no earlier release used (Section 3.6 gives the counts). "Held-back" is also the word of the repository, the task files and the tables that the final run writes. The warning stays. |
| "the answer draws the requested representation on the target and, in the same colour, on other atoms" for spill (cold reader) | Kept "in any colour": spill is judged on the style that the answer itself drew on the target, whether or not that is the requested colour (SI S4.3). |
| Add ClinVar to the sentence on disclaimers (clinical geneticist) | Not done yet: ClinVar's page refuses automated reading (tried again this round), and the paper states no wording that was not read at the source. A PENDING tag for the author marks the place. |
| Boxes 1 and 2 as numbered tables (copy-editor) | Left as boxes until the journal is fixed: it would renumber all 16 tables, and `venues.md` already lists the template check. Box 1 is shorter (background terms are in SI S0). |
| All counts below ten as words (copy-editor) | Done where a reviewer pointed and in the sentences rewritten this round. Counts that are compared with other numbers in the same sentence ("at least 2 of its 3 answers", "in 9 of them ... in the other 6") stay as digits. |
| "N of the 995 controls" for the viewer replay (three) | The check ran on the control set of that day, 850 call-list controls; the paper says 120 of 850 and that 145 were added later. |
| Move the alignment threshold of the name-resolution list to Section 4.1 (structural bioinformatician) | It is in SI Section S4.4 only; the bullet points there. |
| Sort Table 13 by the share of valid answers (ML reviewer) | Kept the order by task success rate, the primary score; the finding now names its columns and gives both correlations. |
| Keep the number of models in the abstract (copy-editor's rewording) | No room within 200 words once SIFTS, ClinVar and UniProt are glossed and the pilot has three sentences; Sections 1 and 5.1 give it. |

### Open, for the lead

1. **`tests/controls/viewer_check.json` should record the sample.** The paper's "120 of 850"
   is worked out, not recorded. A rerun of `scripts/grader_controls.py --viewer-api N` on the
   present 995 controls, with N and the number of controls written into the record, would
   replace the derivation (then run `paper/corpus_values.py --viewer-sample` again, or drop
   it).
2. **ClinVar's statement on clinical use** must be read by hand (PENDING tag in Section 11).
3. **New value keys and specs** on this branch: `clin.*` (traditional names, copies, review
   status, featured list), `corpus.twins.hide_*`, `corpus.twins.no_target.*`,
   `corpus.followup.noop_*`, `controls.viewer.api.*`, `plan.core_models_open/closed`,
   `oct.spec.r_valid_success`, `ex.clinvar_*`; build specs `word`, `date`, `month`. The merge
   with `final-benchmark` must regenerate `corpus_values.json`; if the corpus moved, the
   assertions in `clinical_details` and `pairs_and_followup_details` will say which sentence
   no longer holds.
4. **SI table numbers moved** (S4 to S19) and there is a Section S9 for the final-run tables;
   `scripts/paper_tables.py` writes no numbers into captions, so nothing else follows.
5. **Table 9 titles changed** ("Table 9a. Primary comparison. ..."): see
   `generated/shape_paired.md`.
6. The developer names in Section 5.1 come from a small map in `corpus_values.py` (route
   prefix to company name); check "Alibaba" for the Qwen models and "Z.ai" for GLM.
7. Still open from earlier rounds: items 1, 4, 5, 6 and 8 of round 3.
8. **Layout.** Looked at in the PDF this round, in a build of 42 pages made before the last
   edits (the final build has 43): page 4 (Box 1) and page 24 (nested bullets of Section
   5.4); and page 42 of the SI (45 pages). Figures 1, 2, 3 and 5 were looked at as rendered
   SVG files. The rest of the PDFs was not looked at.

## Round 5 (2026-11-23; fourth round of the third paper branch)

Scores: structural bioinformatician 8, ML benchmark reviewer 8, clinical geneticist 8,
copy-editor 8, cold reader 8. All five would accept on clarity. Two must-fix items.

### Must-fix items, both fixed

- **The "c." notation** (clinical geneticist). Box 1 and Section 3.3.1 now say: nucleotide
  244 of the coding sequence, counted from the A of the start codon ATG.
- **Target precision could not be computed from the main text** (copy-editor; should-fix for
  the four others). Section 4.2 now counts *items* (one style on one atom) and defines
  wanted, credit, attempted, spill and extra, each in one line. "Attempted" is what the code
  counts (`molbench/drawn.py`, `target_display`): the wanted items that the answer drew in
  the right representation, in any colour or opacity. Row S9 of Table 3 is worked by hand in
  the text (24 / 48 = 0.50, score 0.67), the two spill rows in the caption, and SI Section
  S4.3 uses the same words. `corpus_values.py` asserts the numbers of the worked row.

### Should-fix and polish items, fixed

- **"Side" had two meanings** (three reviewers). It now means one of the two tasks of a pair
  and nothing else (Box 1 says so). Section 4 and SI Sections S4.2 and S4.6 say "the other
  drawn state" or name reference and answer.
- **Viewer read-back told three times** (four reviewers). Told once, in Section 4.5, under
  its own heading and in three parts (scene track, call-list track, default view). Section
  3.7 keeps one bullet with the three counts. The caption of Table 4 points to "the text
  below the table" and gives 234 of 240 call lists.
- **Categories and "what the model must know"** (structural bioinformatician). Section 3.3,
  contribution 1 and Section 2.1 now say that four categories differ in what must be known
  and four in the form of the task. The interactions bullet says what differs from
  translation.
- **Copying the number on the call-list track.** Box 1, Section 3.3.1 and planned comparison
  7 say that the property is defined on author numbering and groups results of the scene
  track only.
- **The primary score of the central comparison** (ML reviewer). Sections 5.4 and 6.4
  disagreed. Comparison 7 is now stated once: on the scene track, primary on the target
  score, task success beside it. Table 10 marks the column.
- **"The prediction"** (copy-editor). Section 6.4 says that four patterns are possible and
  that none is predicted; each pattern is stated as the two rows of the table, and "always
  converting" has a concrete case.
- **Intervals on differences and on valid-only scores** (two reviewers). Section 5.4 says how
  each is resampled, which answers JSON mode is set against, and which tracks comparisons 1
  to 6 use. See "Open, for the lead", item 1: part of this is a specification.
- **McNemar's test and clustering** (ML reviewer). Section 5.4 and the caption of Table 9
  say that the test treats pairs as independent; Table 9 has a new column, the difference
  between the one-sided counts with an interval for which structures are resampled.
- **Why a majority of 3 answers.** One sentence in Section 5.4.
- **Target score between the tracks** (ML reviewer). Section 4.2 and SI Section S4.6 say that
  the target score uses the same counts on both tracks and that the more generous rule of the
  call-list F1 is not used for it (`GRADING.md`, "What the viewer does (API track)").
- **Name resolution: two splits described as one** (ML reviewer). Checked with the grader:
  an answer on any panel entry is graded on drawn state, and 3 accepted entries other than a
  reference entry are panel entries. The run records whether the entry is the reference
  entry, so the rows of Table 8 stay as they are; the row labels, the caption, Section 3.3
  and Section 9.3 now say what each row holds and name the 3 entries' exception. SI Section
  S4.4 says how a reference is resolved on another entry (its selections are by kind or by
  compound, never by chain or residue number; checked on all 39 references).
- **A request that states no representation** (structural bioinformatician). Section 3.5:
  on the scene track 3 tasks state none for a ligand and list each representation as an
  accepted answer; on the call-list track a colour alone can be asked. Opacity is not free:
  a reference is opaque unless the request states an opacity (9 tasks); checked with the
  grader.
- **How "the viewer can load the file" is decided** (ML reviewer). Section 4.4: from the
  address and the stated file format, nothing is fetched.
- **Clinical naming** (clinical geneticist). Parentheses, not brackets; what a complete HGVS
  description needs; "p." marks a description at the level of the protein and says nothing
  about numbering; germline is not "inherited"; "wild-type" against "reference"; what a
  matching name in ClinVar is; the two records of the running example are those found through
  UniProt's cross-references, one for each single-nucleotide change; the assumption behind a
  name without an accession; the source of the variants in Section 11; Table 15, row 3. The
  2024 paper on the HGVS nomenclature is cited beside the 2016 one.
- **39, not 46** (two reviewers). Section 3.4 separates the requests with an accession by
  the numbering of the name; new values `clin.n_accession_uniprot` and
  `clin.n_accession_traditional`.
- **Matched tasks and the form of the name** (clinical geneticist). Checked: both tasks of a
  set use the same form; 7 of the 8 sets are in UniProt numbering, and the eighth uses the
  traditional name E6V, where copying is right on the PDB entry and wrong on the predicted
  structure. Table 10 now reports the 7 sets, and its two rows say which is "copying is
  right". `corpus_values.py` asserts all of this.
- **Ten counts in prose** (two reviewers). Table 2b, "Further properties of the clinical
  tasks", with a column on why each matters. The former Table 2 is Table 2a.
- **Section 3.1 too long** (cold reader). The three-step filter is one paragraph with the
  same counts; the steps stay in SI Table S4. The request for p.Ile74Thr is stated.
- **Names for the predecessor** (cold reader, copy-editor). "First version" and "pilot run"
  are defined at the start of Section 6 and used in Sections 3.6, 6.6 and 7, in Table 15 and
  in the heading of Section 6.6. Section 5.1 no longer says that old and new numbers can be
  compared.
- **Box 1** (copy-editor, cold reader, ML reviewer). Moved to the start of Section 3,
  shortened by seven entries that the text defines where they are used (now SI Table S0b),
  and given two rows that the ML reviewer missed: polymer and ligand, and representation
  with "cartoon". The Introduction glosses representation, spacefill and cartoon in a
  sentence, and introduces the two tracks in contribution 3. The abstract glosses cartoon.
- **Abstract** (all five). Short sentences; "in one" category; the question as its own
  sentence; two faults named with their effect. 200 words.
- **Introduction.** The remark on the classification comes after the point of the example;
  the thesis is followed by the benchmark and then by the question; "bare model" defined.
- **Table 3.** Two rows for what is special to the call-list track (C6, the accepted answer
  with the recoloured cartoon segment; C7, the default cartoon hidden), graded by the
  benchmark's grader, and a fourth point in the text.
- **Small things.** Figure 1 caption says "steps"; one entry (1HSG) for the worked example of
  both system prompts, named; 87 distinct variants; the first coordinate set is the first
  "model" in PDB terms, and assemblies are called that (also SI Table S0a); 74 of the 78
  structures; wrong opacity counts half; the APOE example is a case where copying is right;
  the translation sentence; the spin sentence; Finding 1's "them" and "those"; the rating
  sample describes the sample and is no estimate of a false-fail rate (Section 4.5 no longer
  promises one); the Figure 5 caption says why panel C is valid-only; SI Section S4.8 lists
  the same four features as Section 9.3; one table of repository names (SI Table S0c).
- **Figures.** Figure 1, step 2 says what each task gets. Figure 5, panel B: the segments of
  the bar are numbered 1 to 4 and the key is in that order. Figure 6: plain tick labels and
  one axis title.
- **PDF layout.** A table inside a box may break between rows, and a caption is kept in one
  piece with its table.

### Declined, or done differently, and why

| Suggestion | Decision |
|:---|:---|
| Name the RefSeq protein accession of lysozyme (clinical geneticist) | Not typed: no accession is in the frozen data, and the paper states no identifier that a script did not read. The text says what kind of accession a complete description needs. |
| Give the version number of the HGVS nomenclature (clinical geneticist) | The pages read on 2026-11-23 show no version number. The 2024 paper is cited; `related_work_checks.md` records what was read and what was not. |
| "A reader of a protein-level name usually assumes UniProt numbering" | The reviewer is right; rewritten as an assumption of ours that was not checked. |
| Split the rows of Table 8 by grading method (ML reviewer) | The run records "reference entry or not", not "panel entry or not", so the rows stay; captions and text now say that all but 3 of the other entries are compared as written. |
| A weighted estimate of the grader's false-fail rate from the rating sample (ML reviewer, first option) | It would need the image judge's verdict on every failed valid answer, which the plan does not include. The second option was taken: the paper says that no such estimate is made. |
| Spell out every count below ten (copy-editor) | Done at the places named and in rewritten sentences. Counts that sit beside other numbers stay as digits, as in round 4. |
| Delete the draft note under the title (copy-editor) | Kept while PENDING tags are in the text: it explains them. To be deleted with the last tag. The process note of Section 2.3 is cut to one sentence. |
| "Language models are now used to drive ..." (copy-editor) | The abstract has "Language models now drive molecular viewers": the longer form put it over 200 words. |
| Fig. 6 in two panels, or all bar labels in one form (cold reader) | Bar labels stay as in Table 14 (F1 as a number, shares as percentages); the axis was simplified. |
| Figure 5 key in one row (cold reader) | No room at print width; the segments are numbered instead. |
| Move the sentence on DNA-level classification to Section 3.2 only (cold reader) | Done; the Introduction keeps two sentences on the classification, after the example. |

### Corrected although no reviewer asked

- The Figure 1 caption said nothing about the layout; it now says that the steps are in two
  rows (round 5's first wording, "from left to right", was wrong and was caught on the
  rendered figure).
- SI Section S4.3 said that follow-up tasks without a target "take something away or reset a
  setting"; it now matches Section 4.2 (some need no change).

### Open, for the lead

1. **Section 5.4 specifies three computations that `molbench/analysis.py` does not have
   yet.** (a) An interval on valid-only scores (structures resampled with all their valid
   answers; the code has valid-only means without intervals). (b) The difference row of
   Table 10, comparison 7: one draw of structures, both groups recomputed on it, primary on
   the target score. (c) The new last column of Tables 9a and 9b: (scene only − call list
   only) / pairs, with structures resampled. Comparisons 2 to 6 are described as the code
   does them (per-task difference, structures resampled), and comparison 1 as the code does
   it (each split resampled on its own). If any of (a) to (c) is not wanted, the sentence in
   Section 5.4 and the column in `shape_paired.md` must go.
2. **Table 10 reports 7 matched sets, not 8** (`shape_clinical.md`): the set with the
   traditional name E6V is left out, because copying is right and wrong the other way round
   in it. `scripts/paper_tables.py` must follow.
3. **Table 8 row labels changed** (`shape_tiers.md`), and Table 12 rows 2 to 4 say which
   tracks they use (`shape_robustness.md`).
4. **New value keys**: `clin.n_accession_uniprot`, `clin.n_accession_traditional`,
   `clin.n_uniprot_name`, `clin.mature_example.entry/number`,
   `clin.n_offset_pairs_uniprot_name/traditional`, `resolve.n_accepted_entries`,
   `resolve.n_other_panel_entries`, `resolve.n_tasks_with_other_panel_entry`,
   `prompt.worked_example_entry`, `corpus.mvs.n_representation_open`,
   `corpus.mvs.representation_open_example`, `corpus.n_opacity_stated`,
   `ex.n_target_atoms_twice`, `ex.api.default_colour.*`, `ex.api.hide_cartoon.*`. Each has
   an assertion for the sentence that uses it; after the merge, regenerate.
5. **To read at the source before submission** (`related_work_checks.md`, round 5): the HGVS
   pages word for word, and the rule that "c." positions start at the A of ATG.
6. **"First version"** is defined as the benchmark public from May 2026 until the present
   corpus, with the sizes of its last runs (70 scene tasks, 20 call-list tasks). If earlier
   releases had other sizes, the definition still holds, but Dan should confirm the dates.
7. Still open from earlier rounds: items 1, 2 and 6 of round 4.
8. **Length.** The main text grew from about 18,500 to about 20,400 words (45 PDF pages, SI
   47), mostly in Sections 4.2, 4.5 and 5.4. The cold reader asked for less.
9. **Layout.** Looked at this round: Figures 1, 5 and 6 as rendered images, and all 45 pages
   of the main PDF as one contact sheet at low resolution, which shows page breaks and white
   space (no half-empty page seen) but not text. No page was read at full size, and the SI
   PDF was not looked at.

## Round 6 (2026-11-23; fifth round of the third paper branch)

The job that asked for this round called it "round 5"; the log already had a round 5, and
the reviews are of the paper as that round left it (about 20,400 words, 45 pages).

Scores: structural bioinformatician 8, ML benchmark reviewer 8, clinical geneticist 8,
copy-editor 8, cold reader 8. All five would accept on clarity. One must-fix item.

### Must-fix item, fixed

- **The gloss of the target score contradicted its definition** (structural
  bioinformatician). "How well the requested atoms are drawn as asked, whatever else was
  drawn" was wrong for spill and for extra on the target (Table 3, rows S7 to S9). One gloss
  is now used in the abstract, Box 2, Sections 4 and 4.2, the captions of Figures 1, 3, 4 and
  5 and of Tables 3, 6, 9 and 10, and SI Table S1: how far the requested style is on the
  requested atoms and on no others, with unrequested background ignored. *Target-right* is
  glossed in the same words. No "whatever else" is left in the paper or the SI.

### Should-fix and polish items, fixed

- **The four patterns and a table of means** (two reviewers). Section 6.4 now says that the
  patterns describe one model, that the question is answered model by model (rows per model
  in SI Section S9, new PENDING tags), and what "high" and "low" rest on: pattern 1 or 3 when
  the interval of a model's difference lies above or below zero, otherwise the level of the
  two rows is reported and not classified by rule. See "Open, for the lead", item 1.
- **7 sets or 8** (three reviewers). Section 9.4 gives the 7 sets of Table 10 first, with
  their proteins (new value `clin.n_offset_pair_proteins_uniprot_name`), and the 8 in a
  bracket with the reason.
- **"Valid"** (structural bioinformatician). Box 2 states the criterion that is applied:
  the answer obeys the format and the viewer can show it, per track.
- **Call-list target score where the default view already shows the style.** Checked with
  the grader: a load with no further call is target-right in none of the 372 first requests
  of the call-list track (asserted in `corpus_values.py`). Section 4.2 says so and gives a
  paired cartoon request from the corpus as the case in point.
- **Planned comparisons** (three reviewers). Section 5.4: the central clinical comparison
  (comparison 7) has its own bullet, comparisons 1 to 6 are a numbered list, and "totals of
  the two tracks are not compared" is a bullet of its own. Table 12, row 4 is short; its
  detail is in the caption.
- **Rules before the formula** (three reviewers). Section 4.2: three counts, then the three
  rules (rule 1 gives spill, rule 2 extra, rule 3 nothing), then recall, precision and the
  score.
- **Spill** (ML reviewer). Read in the code (`molbench/drawn.py`, `target_display`) and
  checked with the grader: spill is counted on a style of the answer that covers the target
  in the requested representation; the requested representation outside the target in a
  separate style of another colour is unrequested context. Rule 1 and SI Section S4.3 say
  so, and `corpus_values.py` asserts two such answers.
- **A target with several facts** (two reviewers). Section 4.2: recall and precision are
  computed for each part and averaged (as `GRADING.md` and SI Section S4.3 say).
- **Row C7 of Table 3 by hand** (three reviewers), with the reason why its target score
  stays 1; and row C6 passes because the task lists a second accepted answer.
- **Why the call-list F1 follows another rule** (cold reader). One sentence in Section 4.2.
- **Name resolution told once** (four reviewers). Section 4.1 has the full account, with the
  denominator that was missing: 5,778 accepted entries, of which 39 are reference entries, 3
  further panel entries and 5,736 outside the panel (new value
  `resolve.n_accepted_outside_panel`). The bullet of Section 3.3, the caption and the row
  labels of Table 8 and Section 9.3 point to "the weaker rule of Section 4.1".
- **"Primary" had five uses** (cold reader). Box 2 has an entry *Primary score*: which score
  a table or comparison is read on first, and where. The word is now used for scores and
  the comparisons on them only; the groupings are "the grouping on which the question is
  answered" and "for description only", strict is "the default".
- **"Held-back" read as a hidden test set** (two reviewers). The split is now the *set-aside
  split* (Sections 3.6, 5.4, 9.2, 9.4; Table 1 and its caption; Figure 1 and its caption;
  Table 12; SI Tables S0b, S0c and S3). Section 3.6 is three short paragraphs, the point
  first. The complement has no name ("tasks on the other structures").
- **Categories in the order of the text** (cold reader). Figure 2 (two headed columns),
  Table 1 (two headed groups), Table 8, the bullets of Section 3.3 and SI Table S2 list the
  four categories that differ in what must be known, then the four that differ in form.
- **Rendered pictures** (cold reader). Figure 4 opens with the reference, Answer A and Answer
  B as headless Mol\* 5.9.0 renders them, from one camera (`figures.py --viewer-strip`; the
  pictures are committed with the hash of the scenes, and the figure script stops if the
  running example has changed).
- **Conclusion** (cold reader): corpus size, the pairs, and 48 of 82.
- **Clinical naming** (clinical geneticist). "The amino acid that the UniProt canonical
  sequence has at that position", three times; MANE Select named and cited in place of "the
  gene's default transcript"; *qualifying record* and *best-reviewed record* defined
  (Sections 3.1 and 9.2, SI Table S0b); what a request says about the classification, with
  the four wordings and the count of requests that say "pathogenic or likely pathogenic"
  (asserted against every clinical task); germline also for variants better known as
  somatic; Box 1 entries ClinVar, Transcript and Missense variant; "each" record in step 1;
  *mature-protein numbering* as the one name of the numbering of a traditional name.
- **ClinVar's parentheses.** The sentence that gave ClinVar's reason for them is gone. SI
  Section S3.2 describes the title of the running example and says that the requests write
  the protein change without parentheses.
- **HGVS and transcripts** (three reviewers). The two paragraphs of Section 3.3.1 are four
  sentences; the detail is in SI Section S3.2.
- **Step 6 of Section 3.2** says why 82 is right in the call-list reference.
- **Glosses for readers from other fields** (ML reviewer): structure, entry, UniProt,
  ClinVar and SIFTS in the Introduction; Mendelian disease, observed, codon, resolution,
  helix and strand where first used; SIFTS and ClinVar in the abstract.
- **The filter of Section 3.1** is two numbered tests with one count each.
- **26 PDB entries for 25 proteins** and **23 structures against 14**: one clause each, from
  new values.
- **"Entry" for predicted structures**: "structure" in Sections 1, 3.4, 5.2 and 6.4.
- **One name per thing** (copy-editor). "The final run" (no "paid run"); "first-version
  corpus" in Table 14; the heading of Section 6.6; "side" (the other uses reworded, also in
  SI Table S0a); "fact" in its everyday sense is "piece of information"; one punctuation for
  "strict" in the headers of Tables 6, 8 and 13; "plot" in Figure 5; "clarifying question".
- **Small things.** "Further properties", not five; the correlation of Finding 1 is called
  nearly proportional, not a ranking; the title of Table 10; Table 14 has a pooled last
  cell; Section 5.5 as a list with "what the study does not estimate" apart; Section 7's
  first sentence and the title of Table 15; "returned a scene that the viewer could load";
  the pointer after the remark on the classification; the price ranges of Section 5.1;
  citation ranges ("[1–4]"); one link per arXiv reference and one year in reference 1; the
  caption of SI Table S8; Figure 3 says what "structure model" is; Figure 6 has one axis
  title and all bar labels in one form (declined last round; done now, with the caption
  saying that Table 14 gives the shares as percentages).
- **PDF layout.** A heading is kept with what follows it; "6.2 Categories" no longer stands
  alone (looked at on the rendered page).

### Length

Three reviewers asked for a shorter text. Moved to the SI: the HGVS and transcript detail,
what the traditional names leave out, the methods of the panel entries, the colour tolerance
in the pilot run, the template shares, how the viewer sample was drawn. Shortened: the
viewer check of Section 4.5, Findings 1 and 6, the row-9 paragraph of Section 7, Sections
9.2 and 9.3, the name-resolution caveat. Added on request: the classification paragraph of
Section 3.1, row C7 by hand, the per-model reading of Table 10, the glosses, the conclusion.
The balance is about nil: the main text has about as many words as before this round
(`build.py` prints the count). It is not shorter.

### Declined, or done differently, and why

| Suggestion | Decision |
|:---|:---|
| Rename the split "new-structure split" (two reviewers) | The name would be wrong on the facts: 40 of the 63 other structures were also used by no earlier release. What sets the 15 apart is that they were set aside before generation, so the split is called the *set-aside split*. |
| Name both scores and the validity finding in the abstract (cold reader) | No room in 200 words once SIFTS, ClinVar and UniProt are glossed, as another reviewer asked. The abstract names the target score with its gloss; the sentences on the pilot are replaced after the final run. |
| "ClinVar uses the MANE Select transcript in a record's preferred name" (clinical geneticist) | Not written: the ClinVar documentation could not be read at the source this round (`related_work_checks.md`). MANE Select is described from NCBI's page and cited. |
| "This is ClinVar's naming format, not a complete HGVS expression" | Written more narrowly, for the same reason: the SI says what the title looks like and what we take the bracketed protein change to be. |
| A table for the seven planned comparisons (ML reviewer) | A numbered list, as another reviewer proposed; Table 12 already has one row per comparison. |
| Spearman's correlation for Finding 1 | The claim was reworded to what a Pearson correlation shows. No new number was computed for the pilot run. |
| Delete "Both words are used for nothing else" in Box 1 (copy-editor, first option) | The second option was taken: the other uses were reworded, and the sentence stays. |
| State the name-resolution caveat in full in Section 3.3 | It is in Section 4.1 only, as three reviewers asked; Section 3.3 has one sentence. |

### Corrected although no reviewer asked

- Section 3.1 said "(a further 295 were removed)" of candidates that have a pathogenic
  record but none that passes the second test; it now says exactly that.
- The row labels of Table 8 no longer carry the number of panel entries; Section 4.1 does.

### Open, for the lead

1. **Section 6.4 now specifies a per-model reading of Table 10** that no script has yet:
   the first two rows and their difference with a bootstrap interval for each model (SI
   Section S9), and a count of models under each pattern (pattern 1 or 3 by the sign of an
   interval that excludes zero). If this rule is not wanted, the paragraph after the list of
   patterns and the two PENDING tags must go. Item 1 of round 5 (three computations of
   Section 5.4) is still open.
2. **Shape tables changed again**, and `scripts/paper_tables.py` must follow them: the order
   of the categories in Table 8 (`TIERS`); headers "Task success rate, strict", "Target
   score, strict", "F1, strict" (Tables 6, 8 and 13); Table 10 header "Target score (the
   primary score here)" and row labels without "(primary grouping)"; Table 12 rows 1 and 4;
   the two "of which" rows of Table 8.
3. **The repository still says "held back"** (task files, `CORPUS.md`, `TASK_FORMAT.md`);
   the paper says "set-aside" and SI Table S0c maps the two. If Dan prefers the old name, the
   change is a search and replace in `paper/` plus the header of Table 1 in
   `corpus_values.py`.
4. **New value keys**: `clin.n_offset_pair_proteins_uniprot_name`,
   `clin.n_proteins_one_pdb_entry`, `clin.n_haemoglobin_pdb_entries`, `clin.n_class_differs`,
   `clin.n_class_both_word`, `corpus.api.n_first_requests`, `corpus.api.cartoon_example`,
   `resolve.n_accepted_outside_panel`, `oct.spec.highlight_n`, `oct.spec.highlight_exact_n`,
   `oct.spec.highlight_exact`, `ex.mvs.other_colour_around.*`, `ex.mvs.other_colour_beside.*`.
   `corpus_values.py` now grades a load-only answer for every first request of the call-list
   track (372 gradings) on each run.
5. **Figure 4 needs a browser once.** `paper/figures.py --viewer-strip` renders the three
   pictures with `molbench.render` and the Mol\* bundle. In this worktree the bundle was a
   link to the one in the main checkout (git-ignored). If the running example changes at
   the merge, `figures.py` stops and says to run it again.
6. **To check before submission** (`related_work_checks.md`, round 6): the given names of
   the first three authors of Morales et al. 2022, and how ClinVar forms a record's title.
7. **Layout.** Looked at this round as rendered pages of the main PDF (45 pages in its last
   build): the pages with Figures 1, 2, 4 and 6 and Tables 8 and 14, and the page with
   Table 1 as it was before its two group labels were shortened. Not looked at: the other
   pages, Table 1 and Figure 5 in the last build, and the SI PDF.

## After round 6: changes made at the merge (2026-11-23), not reviewed

The paper branch was written on the corpus of 2026-11-16. When it was merged, the text was
brought into line with what had changed since. No reviewer has read these passages:

- **Section 5.1, Box 2, Section 9:** a second script without a model (the literal script)
  beside the keyword script.
- **Section 4.2, SI Sections S4.3 to S4.6 and S4.8:** grader rules added after the provider
  pilot (two coincident representations, the one address of an AlphaFold model, lower-case
  PDB identifiers on the call-list track, half credit only in a style confined to the target,
  target score as the best over accepted answers).
- **Section 4.5 and SI Section S5:** the viewer check as re-run on the present control set.
- **Section 5.5:** rewritten for the rating study as its tooling now builds it (four
  pictures and two verdicts per comparison, three groups by the grader's verdict). The
  earlier text described a design balanced on the image judge.
- **Section 6 (opening) and SI Section S6.1:** the provider pilot, with its one table.

Word count after the merge: about 21,000 (paper) and 9,000 (SI).

## Condensing pass (2026-11-23), after round 6: not reviewed

Five reviewers held the paper at 8 of 10 over six rounds, and each round added words. This
pass did the opposite: the main text was rewritten shorter, and what a reader does not need
in order to follow what was built, why, and how an answer is scored was moved to the
Supporting Information with a one-sentence pointer. No reviewer has read the result.

### Word counts (text outside tables, figure captions and PENDING tags, as `build.py` counts)

| Section | Before | After |
|:---|---:|---:|
| Draft note | 99 | 79 |
| Abstract | 201 | 199 |
| 1 Introduction | 1,148 | 850 |
| 2 Related work | 808 | 319 |
| 3 Building the benchmark | 5,246 | 1,859 |
| 4 Grading on drawn state | 4,547 | 1,935 |
| 5 Experimental setup | 2,805 | 1,110 |
| 6 Results | 3,036 | 1,603 |
| 7 Errors in the first version | 219 | 67 |
| 8 Discussion | 185 | 148 |
| 9 Limitations | 1,579 | 445 |
| 10 Conclusion | 243 | 181 |
| 11 Ethics, 12 Availability, SI list | 477 | 496 |
| **Paper** | **20,594** | **9,291** |
| Supporting Information | 9,006 | 24,182 |

With the text of the PENDING tags, `build.py` prints about 9,700 for the paper. The PDF went
from 45 pages to 28; the SI PDF has 80.

### What moved where

| From the paper | Now in |
|:---|:---|
| Box 1 (two glossary tables) and Box 2 | SI Tables S0d, S0e, S0f. The paper keeps one box of ten terms. |
| 2.1 to 2.3, each related work described | SI Sections S15.1 to S15.3 |
| 3.1: how disease proteins and entries were chosen, counts of proteins and structures | S10.1 (the filter, the two exceptions and the wording of the classification were already in S3.2) |
| 3.3: the eight categories one by one, follow-up turns that need no change, call-only translation tasks | S10.2 |
| 3.3.1: forms of name, HGVS and transcripts, wordings, traditional names with an example, rule for several variants, Table 2b, all matched tasks | S10.3; Table 2b is Table S20; Table 2a is Table 2 |
| 3.4: the notation of a call list, traditional names on the two tracks, pairs by category, the 15 pairs with a switch-off call | S10.4 |
| 3.5 in full (representation, opacity) | S10.5 |
| 3.6 in full (structures used earlier, how the split is read, counts of rephrasings) | S10.6 |
| 4.1: examples of viewer rules, counts of accepted entries | S11.1 |
| 4.2: the call-list rule of F1, the all-3 rate and majority | S11.2 (the two summaries are defined in the captions of Tables 6 and 9) |
| 4.2: counts and three rules of the target score, rule 2 by hand | S4.3 (already there); which atoms are the target, the cost of the convention, the call-list track, the tasks without a target score: S11.3 |
| 4.3: every score of Table 3 worked by hand, row C7, the spill rows of the caption | S11.4 |
| 4.4: the outcomes in full, cut-off answers | S11.5 and Table S5 |
| 4.5: kinds of control, the viewer check in three bullets, what was not checked | S11.6 and S5 |
| 4.6: tolerances | S11.7 |
| 5.1 to 5.6 in full (models, format guides, sampling, every rule of the bootstrap, the six parts of the paired comparison, the rating study with its sampling limits) | S12.1 to S12.6 |
| 6.6: Findings 3 to 6, Table 13 (pilot per model), Table 14 (pilot by category) | S13.1; Tables S21 and S22. The box keeps Findings 1 and 2, Figure 6 and one paragraph on the rest. |
| 7: Table 15 with how each error was found, and the text on row 9 | S13.2, Table S23. The paper keeps a two-column Table 13. |
| 9.1 to 9.4, 22 limitations | S14.1 to S14.4. The paper keeps ten, as a list. |
| 11: Table 16 (licences) | S15.4, Table S24 |

Section numbers of the paper did not change (3.1 to 3.7, 4.1 to 4.6, 5.1 to 5.6, 6.1 to
6.6), because the generated tables and the SI cite them. Section 9 lost its subsections.
The moved text is the round-6 text with its cross-references renumbered; it was not
rewritten, so Sections S10 to S14 repeat some of what S3 to S5 say.

### The standing must-fix: one wording of the target score

Every earlier gloss was false for some row of Table 3 ("on no others" does not cover a second
representation on the residue alone, row S9; "whatever else was drawn" is false for spill,
rows S7 and S8). The wording now used everywhere:

> how exactly the answer marks out the requested atoms. It is 1 (*target-right*) when they
> carry the requested style, no other atom carries that style, and no other representation
> is drawn on them alone; any other drawing, such as a cartoon of the protein, is ignored.

Checked against Table 3: S4 and C4 (wrong colour, 0.50), S5 and S10 (context, 1.00), S7 and S8
(spill, 0.60 and 0.02), S9 (extra on the target, 0.67), C7 (default cartoon hidden, 1.00).
Long form: Section 4.2, Table 3 and Table 9 captions, Figure 3 caption, SI Sections S1 and
S4.3, SI Table S0f. Short form ("how exactly the answer marks out the requested atoms; any
other drawing is ignored"): abstract, Figures 1, 4 and 5, Tables 6 and 10. Task success and
F1 are defined once, in Section 4.2, and repeated only in captions. `paper/README.md` records
the wording.

### Other points of the last review round that this pass settled

- Which score is primary is said once, in one paragraph of Section 4.2 ("Which score is read
  first"); Box 2 is gone.
- The name-resolution caveat is said once (Section 4.1), with its denominator.
- HGVS, transcripts and the default transcript are one sentence in Section 3.3.1.
- The planned comparisons are three separate paragraphs in Section 5.4.
- The pilot findings no longer give a Pearson correlation as evidence about a ranking; the
  box says "nearly proportional".
- The conclusion states the size of the corpus and the paired design.
- A sentence of the pilot box said that a keyword script scored within the range of the
  models; the numbers are 0.72 against 0.72 to 0.95, and the sentence now gives them.

### The result figure

`scripts/paper_figures.py --result-figure DIR` draws Figure 5 from the four result tables
in `DIR` (`table_final_leaderboard_scene`, `_calls`, `_paired`, `_tiers`), so figure and tables
cannot differ. Tested on the dry-run tables: `paper/generated_mock/fig_final_results.svg`,
stamped as mock. Mock tables are refused in `paper/generated`. The paper includes
`generated/fig_final_results.md` when it exists and `figures/fig5_layout.md` (the sketch)
until then. The provider pilot is one sentence at the start of Section 6.

### Open, for the lead

1. **No test covers the new figure command**; tests are outside what this pass could change.
   A test should run it on the mock tables and assert the refusal in `paper/generated`.
2. **Sections S10 to S14 of the SI overlap with S3 to S5.** They should be merged in a pass
   of their own; nothing in them is new.
3. **Tables 6, 9a and 9b still show their first rows only, and Table 7 is a tag**, as before.
4. **The glossary of 5.4 lost its home in the paper**: "all-3 rate" and "majority" are now
   defined only in the captions of Tables 6 and 9 and in SI Table S0f.
5. Items 1 to 7 of round 6 are unchanged. Layout: all 28 pages of the paper's PDF were looked
   at as thumbnails; the SI PDF was not looked at.

## Panel round 1 (2026-11-23): first review of the condensed paper

Five reviewers read the condensed manuscript. No must-fix item; 28 should-fix and 46 polish
items, many of them the same point from several readers.

| Reviewer | Score | Would accept on clarity |
|:---|---:|:---|
| Structural bioinformatician | 9 | yes |
| Reviewer of machine-learning benchmarks | 9 | yes |
| Clinical geneticist | 9 | yes |
| Copy-editor | 9 | yes |
| Cold reader | 9 | yes |

### Length

Text outside tables, figure captions and PENDING tags, as `build.py` counts: **9,289 words**
(9,291 before this round; ceiling 9,500). The fixes needed about 600 words; the same number
was cut elsewhere (list below). With the text of the PENDING tags `build.py` prints about
9,700, as before. Abstract 198 words. The PDF has 27 pages (28 before).

### Should-fix items, all fixed

- **"Never compare between tracks" against Tables 9b and 12** (4.2). Now: track totals are not
  compared on task success and F1; the formats are set against each other on task success
  only in the secondary comparison of Table 9b; "both tracks" in Table 12 means pooled.
- **"We predict none of them"** (6.4). Now: "We state them before the run and do not predict
  which one a model will show."
- **Validity needs the viewer, grading needs no browser** (4.1, 4.4, 5.6, 12). Section 4.4 says
  that validity is decided in a separate step before grading (Mol\* 5.9.0's own validation in
  a browser without a display; loadability from the address alone, nothing fetched). 4.1
  points to it. Section 12 says "grading a validated answer".
- **The extra-against-context convention** (4.2; four readers). The three kinds of drawing
  beyond the request are a list of three, each with its rows of Table 3, and the consequence
  is said outright: ball-and-stick on the target residue alone gives 0.67 (row S9), the same
  on the residue and its two neighbours gives 1.00 (row S10).
- **One wording of the target score, changed once.** "No other representation is drawn on them
  alone" could be read as "only that representation is on them". The long form is now: "…no
  other atom carries that style, and no second representation is drawn on these atoms and
  nowhere else". Changed in Section 4.2, the Table 3 caption, SI Sections S1 and S4.3, SI Table
  S0f and `paper/README.md`; the captions of Figure 3 and Table 9 no longer repeat the long
  form and point to Section 4.2. Checked against rows S4, S5, S7 to S10 and C7 of Table 3.
- **Two things called a pilot** (three readers). "Pilot" now means the pilot run of October
  2026 only. The trial on a few tasks of the present corpus is the *connection test* (Section
  6, SI Section S6.1, the Supporting Information list). The table in S6.1 is written by
  `scripts/paper_tables.py` under the repository's name for it; `INCLUDE_WORDS` in `build.py`
  changes its words, never a number, and fails if the words are no longer found.
- **16 core models against 15 in the pilot run** (all five). Section 5.1 says that 15 ran in the
  pilot run and the other could not be reached that day and had call-list results only; the
  box of 6.6 says "15 of the 16 core models". `STATED_IN_WORDS` holds both numbers.
- **What the set-aside split asks** (3.6; two readers). It asks whether models score higher on
  structures that earlier tasks used; a lower score on the split would suggest so; the test is
  weak (of the 63 other structures only 23 appeared in an earlier release); it is not a hidden
  test set.
- **The 15 pairs that switch off part of the default view** (3.4): one sentence says what the
  request asks for in them.
- **Further findings of the box** (6.6; two readers): they rest on other conditions of the
  pilot run and on a separate run of the first version's call-list tasks in July 2026.
- **The qualifying ClinVar record** (3.1; all five). "Two tests" followed by four conditions is
  now "four conditions", in ClinVar's terms: a variation record that lists the same
  amino-acid change at the same position; classified pathogenic, likely pathogenic or
  pathogenic/likely pathogenic; of the named gene and of that one change alone; review status
  not "no assertion criteria provided". The record lists the change; it does not classify an
  amino-acid change.
- **2,400 variants in the pool, 87 in the tasks, 25 of 27 proteins** (3.1, Figure 1 box 1).
- **Is the model told which sequence a "p." position is counted on?** (3.3.1): 46 requests
  state the UniProt accession, 36 do not, and then neither request nor system prompt says.
- **"64% of all answers"** (6.6): "of the 135 clinical answers".
- **Figure 5, panel A**: "the two scripts" (`figures.py`).
- **"The two cannot be told apart"** (9): the effect of the offset and that of a predicted
  structure.
- **Abstract**: requests "are answered in two formats: a scene description (MolViewSpec) and a
  list of viewer calls (PDBe Mol\*)"; "representation (drawing style)", "residue (amino acid)".
- **Figure 2 caption**: why the 4INS example has several right answers (a Lys29 in each of two
  chains).

### Polish, applied

Table 11 caption defines a turn that needs no change. Trp64: 24 atom records are 14
non-hydrogen atoms and 10 hydrogens, at 1.04 Å. Table 4: "1,020", and why the call-list
controls sit on 74 structures. Figure 1 caption: "the two main ways to average". Name
resolution outside the panel: selections are compared as text. The 31 follow-up tasks without
a target score: why, and that both sides of 8 pairs are among them. The one task in which
copying is wrong without an offset: E6V of haemoglobin beta on a predicted structure. Table 1:
caption and column heads say "remaining + set-aside". Box 1: UniProt's canonical sequence,
initiator methionine included. "Missense" used once. Traditional names: "in which case the
request says …". Table 3, row S2: only the chain name differs in this entry. Table 13 row 3 and
Section 11: the one exception made by hand. Wording: 30 requests are 41 tasks because 11 are
pairs. 4.5: "the reference and the answer of 910 controls". "This is the situation of a model
that is used without tools." Optional models: what "largest" means. OSWorld-Science: PyMOL in
one of its software configurations. Volunteer raters: "one reference and one model answer at a
time". An unshowable answer is defined for both tracks. SI Section S0 is titled "Glossary and
background terms". SI S13.1 no longer mentions the drafting history. Contribution 4: the
analysis of the final run was fixed before any model was called.

### Declined, or done differently, and why

- **"The clinical tasks name 87 of them [the pool]"** (clinical geneticist). Not exact: one of
  the 87 is the exception made by hand and lies outside the pool (SI Section S3.2). The text
  says that the generator draws from the pool and that the tasks name only 87 variants.
- **"No second representation is drawn on exactly the target atoms"** (benchmark reviewer). Not
  exact: *extra* is a style confined to the target, which may cover part of it. The wording
  used is "on these atoms and nowhere else".
- **The connection test "exposed faults in the task files"** (benchmark reviewer). It exposed
  faults of the grader; no request and no reference changed (SI Section S6.1). The text says
  "faults of the present grader".
- **Cut the Figure 1 caption to the pipeline sentence** (copy-editor). Not done: another
  reviewer asked for the full definitions to stay in Figure 1, Table 3 and Table 6. They stay
  there; Figures 3 and 4 and Tables 9 and 10 now point to them.
- **Figure 5 caption, "formats are compared in panel B only"**: kept, since it is a statement
  about the figure and is true of it.
- **"Passes two tests (i), (ii)"** (benchmark reviewer): three other readers asked for four
  conditions, which is what the text now has.
- **27 proteins against 25, in Section 3.3.1** (structural reviewer): said in 3.1 instead, where
  the 27 are introduced; 3.3.1 no longer repeats the number of proteins.
- **Gloss of the interactions category in the text of 3.3**: the sentence that glossed the four
  categories of form was cut; Table 1 and Figure 2 say what each asks.

### Cut to hold the length

The repeated definitions in the captions of Tables 2, 4, 9 and 10; the list of data sources in
Section 2 (the citations moved to Section 3.1); the glosses of four categories in 3.3 (Table 1
has them); the transcript caveat in 3.3.1 (it stays in Section 9 and SI Section S10.3); the
sentence on why some scene tasks have no partner (Table 1 caption has it); 3.7 as a paragraph;
the Pearson correlation in the box (SI Section S13.1 has it); the second statement that track
totals are not compared (5.4); the repeated statement of what a model cannot do (5.2); the
detail of the viewer check (4.5); the list of licensed sources in Section 11 (SI Table S24);
the draft note; small trims in 3.2, 4.3, 5.5, 5.6, 6, 10, 11 and the Supporting Information
list.

### Checked

`python paper/corpus_values.py --check`, `python paper/build.py --check` and `--pdf`;
`pytest tests/test_paper_tables.py tests/test_agreement.py` (68 passed). Figures 1 and 5 were
rendered and looked at after their text changed. All 27 pages of the paper's PDF were looked
at as thumbnails, and pages 4 and 12 (Box 1, Table 3) at reading size. The SI PDF was built
and not looked at.

### Open, for the lead

1. The earlier open items stand (no test for the result-figure command; SI Sections S10 to S14
   overlap with S3 to S5).
2. `molbench/analysis.py` still titles the table of SI Section S6.1 "Provider pilot"; the paper
   changes the words at build time. If the repository takes the paper's name, drop
   `INCLUDE_WORDS`.
3. SI Section S3.2 says that Section 3.1 of the paper "gives the same counts in one paragraph";
   the paper gives the first and the last count only.

## Panel round 2 (2026-11-23): second review of the condensed paper

Five reviewers read the manuscript as it stood after panel round 1. No must-fix item; 19
should-fix and 38 polish items, several of them the same point from more than one reader.

| Reviewer | Score | Would accept on clarity |
|:---|---:|:---|
| Structural bioinformatician | 9 | yes |
| Reviewer of machine-learning benchmarks | 9 | yes |
| Clinical geneticist | 9 | yes |
| Copy-editor | 9 | yes |
| Cold reader | 9 | yes |

### Length

Text outside tables, figure captions and PENDING tags, as `build.py` counts: **9,337 words**
(9,289 before this round; ceiling 9,500). The fixes needed about 270 words and about 220
were cut elsewhere (list below), so the text grew by 48 words. With the text of the PENDING
tags `build.py` prints about 9,750. Abstract 200 words. The PDF has 27 pages, as before; the
SI has 80.

### Should-fix items, all fixed

- **"No second representation is drawn on these atoms and nowhere else"** (4.2, Table 3
  caption, SI Tables S0f and S1, SI Section S4.3; all five readers). The clause parsed two
  ways. Now, everywhere: "when three things hold: the target atoms carry the requested
  style; no other atom carries that style; and no second representation is drawn on target
  atoms alone. Any other drawing, such as a cartoon of the protein, is ignored." The
  *extra* bullet uses the same words ("on target atoms alone"). The Table 3 caption points
  to "the three conditions of Section 4.2" and does not repeat them.
- **"Two exceptions" in 3.1 against "one exception, Section 3.1" in Table 13 and Section
  11** (all five). Section 3.1 now names the one exception to the rule (lysozyme
  p.Ile74Thr, from outside the pool, record without assertion criteria, one task per track)
  and says apart that one pool variant is never asked about (SI Section S3.2). Table 13 row
  3 and Section 11 say what the exception is, so the pointer to Section 3.1 now leads to
  the same statement.
- **Precision of the target score: "the items that the answer spent on marking the
  target"** (benchmark reviewer; three others as polish). Now: "all items that the answer
  drew to mark the target: its items of the requested representation on the target, plus
  spill and extra (formula in SI Section S4.3)". The *extra* bullet gives row S9 in counts
  (24 credited items of 48 drawn, precision 0.50), from generated values.
- **"Qualifying record" meant four conditions in the paper and two in the SI** (clinical
  geneticist, copy-editor). The paper's meaning holds everywhere. SI Table S4 (generated,
  `corpus_values.py`) calls a record that passes step 2 a *matching record*; the text under
  it says that a matching record which also passes 3a to 3c is a qualifying record. SI Table
  S0b cites "the four conditions of Section 3.1". The count of variants with several records
  now says exactly what is counted (records that pass steps 2, 3a and 3b; single-nucleotide
  records only where a variant has one), which is what the script counts.
- **"2,400 ClinVar variants" in Figure 1** (clinical geneticist). The box now reads "2,400
  amino-acid changes with a (likely) pathogenic ClinVar record; the tasks name 87
  variants". Section 3.1 says that a variant here is one amino-acid change, of which ClinVar
  may hold several DNA-level records.
- **"A more generous rule"** (copy-editor; two others as polish). Now with its sense: any
  change to the right atoms earns one half, even in the wrong representation, which earns
  nothing on the scene track.
- **"The weaker rule"** (copy-editor). Renamed the *text rule*, after what it does. Section
  4.1 also says that an answer on an entry the task does not accept scores 0, and the Table 8
  caption says that such answers, and answers that load no entry, are in the category row
  only (checked in `molbench/runner.py`: the flag that divides the two rows is set only for
  accepted entries). The row label of Table 8 is written by `molbench/analysis.py`, which
  this branch does not own, and a test holds it equal to the shape table; `build.py`
  therefore changes the two words when it includes the table (`INCLUDE_WORDS`, which now
  also applies to an `else:` include).
- **"Which score is read first"** (copy-editor, cold reader). The paragraph is headed
  "Which score is primary" and answers in its first two sentences; the reason follows. The
  remark on "both tracks" moved to the Table 12 caption; Table 9b was already described in
  the Table 9 caption.
- **Abstract: "representation (drawing style)"** (cold reader). "Style" is a defined term in
  Section 4.1. Now "representation (spheres, sticks or a ribbon)".

### Polish, applied

Abstract: "Of eight task categories …, one asks"; "classified in ClinVar as". Contribution 4
points to Sections 5 to 7. Related work: "we found no measurement of how accurately they
drive the viewer". One name, *first version*, for what Figure 1, Table 1 and Section 3.6
called an earlier release (SI Table S0b and Section S10.6 too). Box 1 and Section 3.3.1:
the leading segment is a signal peptide, sometimes with a propeptide, or the initiator
methionine alone, which is why E6V is p.Glu7Val. Section 3.1: aggregate germline
classification; "not of a haplotype that carries a second change"; germline "inherited or
newly arisen, not acquired in a tumour"; 87 variants in 82 tasks because a few tasks name
several. Step 4 of 3.2: why the resolution is mentioned. Table 1: "a" before "b", "other" in
place of "remaining" (caption and column heads), why the call-list track has 116 more
translation tasks, and glosses of ligand and disulfide. Section 3.3.1: the 10 helix or
strand tasks, with a gloss, so that Table 10 can point there; "For 7 variants there are two
matched tasks". The 31 follow-up tasks without a target score are left out of every mean of
it (also SI Table S0e, which now says "first request" for the other kind). Table 4: why the
four entries with only DNA or RNA have no call-list control. Section 4.5: 267 of the 300
call lists of the sample. Section 5.1: the core models in one sentence; the literal script
copies the number on a clinical task. Section 5.4: which models a mean over models covers.
Table 10 caption: the first five rows are the groupings, the last three subsets. Headings of
6.5 and 6.6. Section 9: transcript glossed. The connection test moved from the opening of
Section 6 to one sentence in Section 5.6.

Figures (`figures.py`, `scripts/paper_figures.py`): Figure 1, box 6 lists three scores and
then the two averages, in the order of the text. Figure 2: each row of cards is as tall as
its text, and the three glosses that were in the caption (het group, C-alpha, the two
Lys29 of 4INS) are grey lines in their cards. Figures 3 and 5: the two one-sided cells are
blue (right in the scene only) and orange (right in the call list only), as solid fills, in
Figure 3, in the layout of Figure 5 and in the drawn result figure; the hatch patterns are
gone (a pattern fill is lost by some renderers). All four schematics were rendered with the
Chromium that builds the PDF and looked at, as were pages 6 and 17 of the PDF and the mock
result figure.

### Declined, or done differently, and why

- **"Lysozyme p.I74T"** (structural reviewer): written p.Ile74Thr, the form of the SI.
- **"Any change to a right atom earns at least half credit"** (benchmark reviewer): the rule
  of SI Section S11.2 is one half for a change to another result and 1 for the same result;
  the text gives it in those words.
- **Heading "Follow-up turns, open requests and planned comparisons"** (copy-editor): "open"
  is not used, because open-ended requests are a different thing, which the corpus leaves
  out (Table 13, row 6). The heading is "Follow-up turns, several right answers, planned
  comparisons".
- **Connection test to the SI only** (cold reader): one sentence stays in Section 5.6,
  because it discloses that the test exposed faults of the grader.
- **"If there really were several releases, say so once"** (benchmark reviewer): said in
  the SI (Table S0b, Section S10.6: "in any of its releases"); the paper says "never used".
- **A change of what the count of variants with several records counts** (clinical
  geneticist offered either): the count is unchanged and its description is made exact.

### Cut to hold the length

Section 3.7 to two sentences (Figure 1 states the four checks). The second statement of the
target-right conditions in the Table 3 caption. The list form of the six planned comparisons
in 5.4 (Table 12 has the rows). The groups of the rating study in one clause, and the
sentence on its trial (Section 6.6 has it). Two sentences of the grader bullet and one of
the small-groups bullet in Section 9 (Section 4.5 and SI Section S14 have them). Small trims
in 3.6, 4.4, 4.5, 5.1, the Conclusion and the Supporting Information list.

### Checked

`python paper/corpus_values.py --check`, `python paper/build.py --check` and `--pdf`;
`pytest tests/test_paper_tables.py tests/test_agreement.py` (68 passed).
`scripts/paper_figures.py --result-figure paper/generated_mock` still draws the mock figure.

### Open, for the lead

1. `molbench/analysis.py` writes the Table 8 row label with "weaker rule"; the paper changes
   the words at build time. If the repository takes the paper's term (*text rule*), change
   the label there and in `corpus_values.py` together and drop the entry in `INCLUDE_WORDS`.
2. The earlier open items stand (no test for the result-figure command; SI Sections S10 to
   S14 overlap with S3 to S5; "Provider pilot" in `molbench/analysis.py`).
3. Item 3 of panel round 1 is closed: SI Section S3.2 now says what Section 3.1 gives.

## Panel round 3 (2026-11-23): third review of the condensed paper

Five reviewers read the paper after panel round 2. No must-fix item was raised.

| Reviewer | Clarity score | Would accept on clarity |
|---|---:|---|
| Structural bioinformatician | 9 | yes |
| Benchmark reviewer | 9.5 | yes |
| Clinical geneticist | 9.5 | yes |
| Copy-editor | 9.5 | yes |
| Cold reader | 9.5 | yes |

### Length

Text outside tables, figure captions and PENDING tags, as `build.py` counts: **9,489 words**
(9,337 before this round; ceiling 9,500). The fixes needed about 310 words and about 160
were cut elsewhere (list below). With the text of the PENDING tags `build.py` prints about
9,920. Abstract 200 words.

### Should-fix items, all fixed

- **The rule of Section 6.4 did not match the four patterns** (structural reviewer). The
  paragraph no longer assigns a pattern by rule. For each model the two row means and the
  interval of their difference are reported; an interval above zero points towards pattern
  1, one below zero towards pattern 3, and one that includes zero leaves patterns 2 and 4,
  between which no threshold is set. The PENDING tag asks for the number of models with an
  interval above, below and across zero, with the levels.
- **"267 of the 300 call lists"** (four reviewers). Section 4.5 now says: a sample of 150
  controls holds 300 call lists; 267 were replayed and every one agreed; the other 33 were
  not replayed (27 select by UniProt number), so none disagreed. New value
  `controls.viewer.api.lists_not_replayed`. SI Section S5 keeps the full breakdown (27, 3, 3).
- **23 structures against 14** (structural reviewer). Section 3.6: "appeared in any task of
  the first version (its pilot run, of scene tasks alone, used 14 structures)".
- **The ClinVar terms of Section 3.1** (benchmark reviewer). Aggregate classification,
  haplotype and "no assertion criteria provided" are each glossed in a clause; *missense*
  and *germline* have a sentence of their own (clinical geneticist). Section 9: "without
  naming the disease".
- **87 variants, "one of them"** (clinical geneticist). "86 from the pool and one exception
  made by hand from outside it, lysozyme p.Ile74Thr, among the first variants reported to
  cause lysozyme amyloidosis". New value `clin.n_variants_from_pool`. Figure 1, box 1, says
  the same, and "pathogenic or likely pathogenic" in full.
- **Three floats never cited in the text** (copy-editor). Figure 5 is cited at the opening of
  Section 6, Tables 6 and 7 in 6.1, Tables 11 and 12 in 6.5.
- **Box 1, traditional name** (all five). Two sentences; the example W64R stands with the
  definition and not with the initiator methionine.
- **16 core models against 15 in the pilot run** (all five). Section 5.1: the core models are
  those of the first version's online results browser in October 2026; 15 are in the pilot
  run, "and the other could not be reached on the day of that run".

### Polish, applied

Abstract: "the variant's name"; "the protein's reference sequence (UniProt)"; "cartoon
ribbon"; "errors" for faults and flaws, here, in contribution 4 (with "Table 13, rows 1 and
2") and in Section 6.6. Figure 1 caption: cartoon glossed; box 1 says what the 78 and the
79 are. Box 1: label numbering counts along the full sequence, residues without coordinates
included. Section 3.2, step 4: "otherwise" stands next to the check; the notation Trp64 is
explained. Table 1 caption: why name resolution has no call-list task (the scene grader can
compare as text; a call list cannot be replayed without atoms). Section 3.3.1: the sentence
on E6V in three short ones. Section 3.4: PDBe expanded; Figure 3 caption: the note on
"structure model" moved up. Section 3.6: the first version defined at its first use in the
body. Section 3.7 names the four checks. Section 4.1: "the separate check, made before
grading". Section 4.2: the three kinds of drawing beyond the request come before the
sentence on precision; "the target score is used between the formats because". Section 5.3:
*cut off* defined. "Wording" for phrasing, rewording and rephrasing (3.6, 5.4, 9). Table 10
caption: which rows are the groupings. Table 11 caption: the two tracks must not be compared
on task success. Table 12 title. Figure 4, Answer B: the credit of each fact (0.5 and 0)
and the sum in the precision row; the script asserts that the sum is the graded value.

### Declined, or done differently, and why

- **A valid call list: "every call and every field is documented"** (copy-editor). The
  check (`molbench/schema.py`, GRADING.md) does not reject an undocumented field; it rejects
  an unknown call, a missing required field, a wrongly typed value and a representation
  name outside the viewer's list. Section 4.4 and the Table 7 caption now say that, and no
  longer say that every field must be documented.
- **"14 of them in its scene tasks"** (structural reviewer). No frozen file shows that the
  14 structures of the pilot run are all among the 23, so the text gives the 14 without
  calling them a subset, as SI Section S10.6 does.
- **"The sixteenth was added to the public results after that run"** (two reviewers offered
  it as a guess). The true reason, from SI Section S12.1, is given: it could not be reached
  on that day.
- **Closing the quotation marks in Figure 3** (structural reviewer). They were closed in the
  file; ImageMagick drops a quotation mark at the end of a line. The call-list panel now has
  no quotation marks, like the scene panel (the reviewer's alternative), so it reads the
  same in every renderer.
- **The cold reader's wording of the abstract** ("that a named disease variant replaces; the
  variants are classified ...") did not fit the 200 words; the sentence is "the residue
  (amino acid) replaced by a variant that ClinVar classifies as pathogenic or likely
  pathogenic. The variant's name ...".
- **Figure 4, a separate line for the sum**: it did not fit the panel; the sum is in the
  label of the precision row.

### Cut to hold the length

The recolouring of the default cartoon in Section 3.2 to one clause (SI Section S1 has it);
the list of what SI Section S3.2 and S10.3 hold; the second statement of the two further
rows of Table 8 in Section 4.1; the definition of target-right in the Table 3 caption
(Section 4.2 is on the same page); "a lower score on the split would suggest so" (3.6);
the archive of raw answers in 5.3 (Section 12 and Table 13, row 8, have it); the closing
sentence of the first Discussion point; small trims in 3 (opening), 3.4, 5.6, 10 and 11.

### Checked

`python paper/corpus_values.py --check`, `python paper/build.py --check` and `--pdf`;
`pytest tests/test_paper_tables.py tests/test_agreement.py` (68 passed). Figures 1, 3 and 4
were rendered with the Chromium that builds the PDF and looked at; Figure 3 also with
ImageMagick. The PDF pages were not looked at in this round.

### Open, for the lead

1. The earlier open items stand.
2. Whether the 14 structures of the pilot run are all among the 23 could be settled from the
   pilot archive; the text does not depend on it.
