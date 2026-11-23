## 9. Limitations

Four limits bound the claims of this paper more than the others: each track is graded by the
rules of one viewer; the requests come from templates; the tasks are public; and the grader
has been tested only against cases that we foresaw. The full list follows in four groups.

### 9.1 Scope

- **One viewer per track.** The scene track is graded by the rules of Mol\* 5.9.0, and the
  call-list track by those of PDBe Mol\* 3.3.2. MolViewSpec is designed to be independent of the
  viewer, but Mol\* is its implementation in practice. We make no claim about PyMOL, ChimeraX
  or VMD.
- **No lookup, one answer.** A model cannot look anything up, ask a clarifying question, or see the picture.
  A product that wraps a model in tools, validation and retries may do better. We measure the
  model, not such a product.
- **No open-ended tasks.** Requests such as "show the active site clearly" have no single
  right drawn state and are not in the corpus. Requests with a countable ambiguity are, in a
  small category.

### 9.2 Corpus

- **Generated requests.** Requests come from templates. They are cleaner than what people
  type. They have been read for naturalness by the authors and by the language-model reviewers
  of Section 7, not yet by an independent structural biologist. The terse and indirect
  phrasings were written out one by one by the language-model coding assistant used in this
  work, and checked by rule for dropped values; no person has read them all.
- **Public tasks and contamination.** Earlier MolBench tasks have been public since May 2026,
  and the whole corpus, set-aside split included, was in a public repository before the run. A
  model trained later may have seen any of it. The set-aside split does not solve this: it
  compares two sets of structures, not seen tasks with unseen tasks (Section 3.6). It cannot
  show that a model has, or has not, memorised tasks, and it cannot protect future runs. The
  generators are seeded, so a fresh split on new structures can be generated.
- **A panel of {{panel.n}} structures.** The structures were chosen by hand for coverage and
  are mostly well known: the median year of deposition is {{panel.deposited_median}}, and only
  {{panel.n_deposited_2020_on}} entries date from 2020 or later. Scores on them may be higher
  than on a recent entry that a model has never read about. All but
  {{panel.n_over_size_limit}} entries have at most {{panel.max_atoms:,}} atoms, so large
  assemblies are not tested.
- **Classifications change, and sources differ.** ClinVar classifications change as evidence
  is submitted. Ours are a snapshot of {{variants.clinvar_retrieved:date}} to
  {{variants.records_retrieved:date}}. Sources also differ on one day: for
  {{variants.removed_share:.0%}} of the candidates that UniProt lists as pathogenic or likely
  pathogenic, none of the ClinVar records that UniProt cross-references gives the same
  amino-acid change such an aggregate classification (Section 3.1). The residue that a name
  points to does not depend on the classification, and no task asks for a judgement about
  disease.
- **Records with little review.** The clinical requests name {{clin.n_variants}} distinct
  variants (a variant that is asked about on two structures is counted once). For
  each variant we take its *best-reviewed record*: of its qualifying records (Section 3.1),
  the one with the highest review status. For
  {{clin.review.single}} variants, the running example among them, this record has the review
  status "{{ex.clinvar_review_status}}": one submitter, with stated
  criteria, and no confirmation by a second submitter or an expert panel. For
  {{clin.review.multiple}} it has several submitters and no conflicts, and for
  {{clin.review.expert_or_guideline}} it was reviewed by an expert panel or comes from a
  practice guideline. One variant, lysozyme p.Ile74Thr, is used although its record states
  no criteria (Section 3.1).
- **What we did not check in ClinVar.** We looked only at the ClinVar records that UniProt
  cross-references. A record lists the protein change once for each transcript of the gene;
  we accept it if any one of these names equals our amino-acid change and position, and we
  did not check which transcript that name is counted on. If it numbers the protein
  otherwise than the UniProt canonical sequence does, the record is about another residue
  than the one we ask for; the reference atoms would still be those of the UniProt position
  in the request. A request that states no accession rests on the same assumption for the
  protein of the gene's MANE Select transcript (Section 3.3.1). A request also attaches
  ClinVar's classification to a protein-level name and names no condition, which ClinVar
  itself does not do (Section 3.1). And one qualifying record is enough: we did not look for
  further records of the same amino-acid change that are classified differently.

### 9.3 Grader

- **Tested only against cases we foresaw.** The grader makes no error on the control set
  because it was corrected until it made none (Section 4.5). How often it misjudges a way of
  writing an answer that the control set lacks is not known. The human check of the grader has
  so far been run only as a trial with {{pilot.n_raters:word}} raters (Section 6.6). Until the
  planned study is done, the evidence that task success matches what people see is the control
  set and the read-back from the viewers.
- **UniProt selections were not replayed in the viewer.** The call-list references of the
  clinical category select by UniProt accession and position. The grader resolves these
  through the frozen SIFTS table; for PDB entries this path was not compared with the running
  viewer (Sections 3.4 and 3.7).
- **Name resolution: text comparison outside the panel.** Of the
  {{resolve.n_accepted_entries:,}} entries that the name-resolution tasks accept,
  {{resolve.n_accepted_outside_panel:,}} are outside the panel, and an answer on one of them
  is compared with the reference as text, so a correct answer that is spelled differently
  fails (the weaker rule of Section 4.1). Table 8 reports such answers in a row of their
  own.
- **The file behind the call-list viewer.** The atom tables are built from the archive file of
  each entry, and the read-back loaded that file into both viewers. Left to itself, PDBe Mol\*
  fetches PDBe's own copy of the entry, which carries the SIFTS mapping. We did not compare
  the two copies atom record by atom record.
- **Partial credit is a choice.** Facts have equal weight, and a wrong colour or opacity
  counts half. On
  the call-list track any other change to the right atoms counts half as well, so F1 is not
  the same measure on the two tracks (Section 4.2). Other choices would give other F1 values.
  Task success does not depend on them.
- **What the grader does not model.** Atoms are compared on the coordinates as deposited;
  selections of single symmetry copies of a biological assembly are not modelled. The
  appearance of labels, sizes and camera coordinates are not graded. Four features of the
  call-list viewer that fetch data from live services are graded only as settings that the
  answer switched on. SI Section S4.8 gives the full list.

### 9.4 Run

- **What the run can and cannot detect.** Means per category and track rest on
  {{corpus.tier_tasks_min}} to {{corpus.tier_tasks_max}} tasks (Table 8); the smallest
  categories are estimated loosely. Several planned
  contrasts are descriptive only: the set-aside split against the other tasks within one
  category (the set-aside tasks sit on {{corpus.heldback.n_structures}} structures); the
  {{clin.n_sse}} helix and strand tasks; the terse and indirect phrasings within one category
  ({{corpus.n_requests_paraphrased}} requests in all); and the matched clinical tasks. Table
  10 reports {{clin.n_offset_pairs_uniprot_name}} sets of matched tasks, on
  {{clin.n_offset_pair_proteins_uniprot_name}} proteins. ({{clin.n_offset_pairs}} sets ask
  about the same variant on a structure with an offset and on one without; one of them uses
  a traditional name and is left out, Section 3.3.1.) In every set the structure without an
  offset is a predicted structure, so "no offset" and "predicted structure" cannot be told
  apart. We report these contrasts with intervals and do not test them.
- **The viewer can do the mapping on one track only.** On the call-list track the viewer can
  map a UniProt position itself; on the scene track the model must. The paired comparison is
  therefore reported with and without the clinical pairs (Sections 3.4 and 6.3).
- **The two system prompts differ in length.** The system prompt has {{prompt.mvs.words:,}}
  words on the scene track and {{prompt.api.words:,}} on the call-list track (Section 5.2),
  and in the pilot run a longer prompt lowered the share of valid answers. A difference
  between the tracks can therefore come from the prompt as well as from the format.
- **Structures of one protein are resampled separately.** Intervals resample structures. In
  the clinical category, {{clin.n_proteins_several_structures}} proteins have tasks on more
  than one structure, and matched tasks ask about the same variant on two structures. Such
  structures are not independent, so intervals in this category are somewhat too narrow.
- **The floor.** The keyword script is a weak floor. The literal script is a stronger one:
  with no knowledge of any structure it solves a share of the
  translation category, and in the clinical category copying the number in the variant name
  is right in {{clin.n_face_value_right}} of the {{clin.n}} tasks (Section 3.3.1). Clinical
  results are therefore grouped by that property, and follow-up results by whether the right
  answer is to change nothing.
- **Prices and hosted models change.** Costs are list prices on the day of the run. Hosted
  models are updated and withdrawn; the archived answers are the lasting record.
