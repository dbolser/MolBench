## 9. Limitations

Four limits bound the claims of this paper more than the others: each track is graded by the
rules of one viewer; the requests come from templates; the tasks are public; and the grader
has been tested only against cases that we foresaw. The full list follows in four groups.

### Scope

- **One viewer per track.** The scene track is graded by the rules of Mol\* 5.9.0, and the
  call-list track by those of PDBe Mol\* 3.3.2. MolViewSpec is designed to be independent of the
  viewer, but Mol\* is its implementation in practice. We make no claim about PyMOL, ChimeraX
  or VMD.
- **Closed-book, one answer.** A model cannot look anything up, ask back, or see the picture.
  A product that wraps a model in tools, validation and retries may do better. We measure the
  model, not such a product.
- **No open-ended tasks.** Requests such as "show the active site clearly" have no single
  right drawn state and are not in the corpus. Requests with a countable ambiguity are, in a
  small tier.

### Corpus

- **Generated requests.** Requests come from templates. They are cleaner than what people
  type, and they have been read for naturalness by the authors and by the reviewers of the
  corpus (Section 7), not yet by an independent structural biologist. The terse and indirect
  phrasings were written out one by one by the language-model coding assistant used in this
  work, and checked by rule for dropped values; no person has read them all.
- **Public tasks and contamination.** Earlier MolBench tasks have been public since May 2026,
  and the public split of this corpus will be public when the paper is. A model trained later
  may have seen them. The held-back split does not solve this. Its tasks were in a public
  repository for some days before the run, and nearly all tasks in both splits are new, so it
  compares structures that earlier MolBench tasks had used with structures that none had used,
  not seen tasks with unseen tasks (Section 3.6). Three of its structures share a protein with
  a public structure. It cannot show that a model has, or has not, memorised tasks, and it
  cannot protect future runs. The generators are seeded, so a fresh split on new structures
  can be drawn.
- **A panel of {{panel.n}} structures.** The structures were chosen by hand for coverage and
  are mostly well known: the median year of deposition is {{panel.deposited_median}}, and only
  {{panel.n_deposited_2020_on}} entries date from 2020 or later. Scores on them may be higher
  than on a recent entry that a model has never read about. All but
  {{panel.n_over_size_limit}} entries have at most {{panel.max_atoms:,}} atoms, so large
  assemblies are not tested.
- **Clinical labels move.** ClinVar classifications change as evidence is submitted. Ours are
  a snapshot of {{variants.clinvar_retrieved}} to {{variants.records_retrieved}}. For
  {{variants.removed_share:.0%}} of the candidates, ClinVar's classification already differed
  from the label we started from (Section 3.1). Several of the variants we use, including the
  running example, rest on records whose review status is "{{ex.clinvar_review_status}}". The
  benchmark uses a variant only as an address: which residue does this name point to? That
  address does not depend on the classification. No task asks for a judgement about disease.
- **The format gap in the clinical pairs.** On the call-list track the viewer can map a UniProt
  position itself; on the scene track the model must. The paired comparison is therefore
  reported with and without clinical pairs. The two system prompts also differ in length,
  because the two format references do, and in the pilot run a longer prompt lowered the share
  of valid answers. A difference between the tracks can therefore come from the prompt as well
  as from the format.

### Grader

- **Tested only against cases we foresaw.** The grader makes no error on the control set
  because it was corrected until it made none (Section 4.5). How often it misjudges a way of
  writing an answer that the control set lacks is not known. The human check of the grader has
  so far been run only as a pilot with {{pilot.n_raters}} raters (Section 6.6). Until the
  planned study is done, the evidence that task success matches what people see is the control
  set and the read-back from the viewers.
- **Name resolution: text comparison outside the panel.** A request that names a protein
  accepts any PDB entry of it. Only panel entries have frozen atom tables, so on any other
  accepted entry an answer's selections are compared with the reference's as text. The common
  ways of writing "the protein" pass; a correct selection by chain identifier does not. The
  tier's results are reported apart for answers on the reference entry and on any other
  accepted entry.
- **Partial credit is a choice.** Facts have equal weight, and a wrong colour counts half.
  Other choices would give other F1 values. Task success does not depend on them.
- **What the grader does not model.** Atoms are compared on the deposited model; single copies
  in a symmetry-built assembly are not modelled. Label styling, sizes and camera numbers are
  not graded. Views of the call-list viewer that need live services (superposition, ligand
  view, annotations, density maps) are graded as declared settings; the atoms they would draw
  are not modelled. SI Section S4.8 gives the full list, including four call-list actions that
  one host of the viewer ignores.

### Run

- **What the run can and cannot detect.** Track totals and tier means rest on dozens to nearly
  two hundred tasks and are estimated with useful precision. Several planned contrasts are
  descriptive only: the public against the held-back split within one tier (held-back tasks
  sit on {{corpus.heldback.n_structures}} structures); the {{clin.n_sse}} helix and strand
  tasks; paraphrases within one tier ({{corpus.n_requests_paraphrased}} requests in all); and
  the matched clinical tasks. Of the last there are {{clin.n_offset_pairs}} sets that ask the
  same variant on a structure with and on one without an offset, on
  {{clin.n_offset_pair_proteins}} proteins, and the structure without an offset is always a
  predicted model, so "no offset" and "predicted model" cannot be told apart. We report these
  contrasts with intervals and do not test them.
- **The floor.** The keyword script is a weak floor. A script of regular expressions over the
  request templates, with no knowledge of any structure, would solve a share of the
  translation tier, and on the clinical tier the number in the variant name is the right
  author number in {{clin.n_face_value_right}} of the {{clin.n}} tasks (Section 3.3). Clinical
  results are therefore split by that property, and follow-up results by whether the right
  answer is to change nothing.
- **Prices and hosted models change.** Costs are list prices on the day of the run. Hosted
  models are updated and withdrawn; the archived answers are the lasting record.
