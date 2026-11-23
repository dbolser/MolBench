## 9. Limitations

The limits that bound the claims of this paper most are listed here; SI Section S14 gives
the full list with numbers.

- **One viewer per track.** Answers are graded by the rules of Mol\* 5.9.0 and of PDBe Mol\*
  3.3.2. We make no claim about PyMOL, ChimeraX or VMD.
- **A model alone.** A model cannot look anything up, ask a question or see the picture. A
  product that wraps a model in tools, validation and retries may do better.
- **Requests from templates.** They are cleaner than what people type, no independent
  structural biologist has yet read them for naturalness, and open-ended requests ("show
  the active site clearly") are left out.
- **Public tasks.** The whole corpus, set-aside split included, was public before the run,
  so no part of it can show whether a model has memorised tasks.
- **A small panel of well-known structures.** The {{panel.n}} structures were chosen by
  hand; the median year of deposition is {{panel.deposited_median}}. Scores may be higher
  than on recent or very large structures.
- **ClinVar is a snapshot, read through UniProt.** Classifications change. We looked only at
  the records that UniProt cross-references, did not check which transcript a record's
  protein-level name is counted on, and attach the classification to a protein-level name
  without a condition, which ClinVar itself does not do. The residue that a name points to
  does not depend on the classification.
- **The grader is tested only against cases that we foresaw.** It makes no error on the
  control set because it was corrected until it made none. Until the rating study is done,
  the evidence that task success matches what people see is the control set and the
  read-back from the viewers. Selections by UniProt position were not replayed in the
  viewer, and name-resolution answers outside the panel are compared as text.
- **Partial credit is a choice.** Equal weight for facts and half credit for a wrong colour
  are conventions, and F1 is not the same measure on the two tracks. Task success does not
  depend on them.
- **The formats are not compared on equal terms everywhere.** The call-list viewer can map a
  UniProt position itself, and the two system prompts differ in length
  ({{prompt.mvs.words:,}} and {{prompt.api.words:,}} words).
- **Small groups are descriptive only.** The set-aside split within one category, the
  matched clinical tasks, the helix and strand tasks and the two rephrasings are reported
  with intervals and not tested. In every set of matched tasks the structure without an
  offset is a predicted structure, so the effect of the offset cannot be told apart from
  that of a predicted structure. Structures of one
  protein are resampled separately, so intervals in the clinical category are somewhat too
  narrow.
