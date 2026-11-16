## 7. What we got wrong and changed

The benchmark of Section 3 is the second version of most of its parts. We list what the first
version got wrong, how we found out, and what replaced it, because each error is one that
another benchmark of this kind could make.

1. **References drew more than the request asked.** Our clinical references added a grey
   cartoon behind the requested residue. Models were then scored on reproducing scenery they
   had not been asked for, and we read the low score as a difficulty of the lookup. An error
   analysis of the pilot run exposed it (Section 6.6, Finding 2). *Change*: a reference holds
   only what the request states, and the target score is reported with every result.
2. **The clinical tier could not test what it was for.** It had
   {{mvs.spec.regime.Clinical.n_tasks}} tasks on one protein whose structure is numbered as
   UniProt is. *Change*: {{clin.n}} tasks on {{clin.n_proteins}} proteins and
   {{clin.n_structures}} structures; {{clin.n_offset}} targets have an offset, and results are
   split by whether the number in the variant name is the author number.
3. **"Pathogenic" was taken from a secondary source.** We first took variants that UniProt
   lists as pathogenic. ClinVar's aggregate classification disagreed for
   {{variants.removed_share:.0%}} of them, and some variants named in our earlier tasks are now
   classified as conflicting. *Change*: every variant is confirmed against ClinVar's own
   record, and the date is stored (Section 3.1).
4. **The graders compared text.** The first scene grader compared scene trees path by path. It
   failed {{controls.mvs.old.false_fail}} of {{controls.mvs.old.false_fail_n}} correct control
   answers that were merely written differently. The first call-list grader compared call
   sequences. It passed {{controls.api.old.false_pass}} of {{controls.api.old.false_pass_n}}
   wrong control answers and failed {{controls.api.old.false_fail}} of
   {{controls.api.old.false_fail_n}} correct ones, and a keyword script scored close to the
   models (Section 6.6, Finding 5). *Change*: both tracks are graded on drawn state, and the
   control set is run as a test on every change.
5. **Hand-written call-list tasks had errors.** A check of those references against the
   structures found label numbers where author numbers were meant, and one task was the worked
   example of the prompt. *Change*: every reference is generated, replayed in the real viewer
   on a sample, and the prompt's example structure is excluded from the corpus.
6. **Some requests had no single answer.** An early request to highlight "all pathogenic
   residues" of one protein resolved to 204 residues, which no user means. "Show me lysozyme"
   was graded against one arbitrary view. *Change*: clinical requests name each variant;
   requests with a countable ambiguity have their own tier with every accepted state listed;
   open-ended requests are left out (Section 9).
7. **Raters could not see what they were rating.** In the pilot rating study, a single
   highlighted residue on a whole complex was a few pixels wide; a volunteer flagged the
   reference as wrong when it was only unreadable. A volunteer also found references in which
   two cartoons overlapped. *Change*: pictures are framed on the target atoms from one shared
   camera; overlapping references were corrected; the next study completes two ratings per
   pair before opening new pairs.
8. **One sample, few structures, a short output limit.** The pilot drew one sample per task on
   {{mvs.n_structures}} structures, with an output limit of 2,000 tokens and no record of how
   often an answer was cut off. *Change*: {{plan.samples}} samples, {{corpus.n_structures}}
   structures, a limit of {{plan.max_tokens:,}} tokens, and the finish reason archived for
   every call.
9. **The prompts taught answers that the graders marked wrong.** Before the final run, four
   independent audits wrote natural answers by hand and graded them. The worked example of the
   scene prompt selected a named compound in a way the references did not; the worked example
   of the call-list prompt coloured a residue in a form that many generated tasks did not
   accept; a residue named by UniProt number on a predicted model was scored as selecting
   nothing; and a scene with an unreadable file passed. The same audits found clinical requests
   whose "pathogenic" record belonged to another gene or to a pair of variants
   (Section 3.1). *Change*: each finding was fixed in the generator or grader and is pinned by
   a test and a control kind, and both prompt examples are graded by the benchmark's own
   grader as a test.
