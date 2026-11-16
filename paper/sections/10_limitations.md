## 9. Limitations

- **One viewer per track.** The scene track is graded by the rules of Mol\* 5.9.0, and the
  call-list track by those of PDBe Mol\* 3.3.2. MolViewSpec is designed to be independent of the
  viewer, but Mol\* is its implementation in practice. We make no claim about PyMOL, ChimeraX
  or VMD.
- **Call-list actions that one host ignores.** The call-list track grades what each call does
  in PDBe Mol\* 3.3.2. The notebook widget that hosts this viewer for Python users (ipymolstar
  0.1.0) has no handler for four of the actions (camera focus, setting the highlight colour,
  clearing the highlight and clearing the selection); there they do nothing. Views that need
  live services (superposition, ligand view, annotations, density maps) are graded as declared
  settings; the atoms they would draw are not modelled.
- **Public tasks and contamination.** Earlier MolBench tasks have been public since May 2026,
  and the public split of this corpus will be public when the paper is. A model trained later
  may have seen them. The held-back split is on structures that no earlier MolBench task used,
  but its tasks were in a public repository for some days before the run, three of its
  structures share a protein with a public structure, and almost no public task of this corpus
  was published before either. It compares familiar with unfamiliar structures and cannot show
  that a model has, or has not, memorised tasks; it cannot protect future runs at all. The generators are seeded, so a fresh split on new
  structures can be drawn.
- **A panel of {{panel.n}} structures.** The structures were chosen by hand for coverage and
  are mostly well known: the median year of deposition is {{panel.deposited_median}}, and only
  {{panel.n_deposited_2020_on}} entries date from 2020 or later. Scores on them may be higher than on a recent
  entry that a model has never read about. Entries above {{panel.max_atoms:,}} atoms are
  excluded, so large assemblies are not tested.
- **Clinical labels move.** ClinVar classifications change as evidence is submitted. Ours are
  a snapshot of {{variants.clinvar_retrieved}}. For {{variants.removed_share:.0%}} of the
  candidates, ClinVar's aggregate classification already differed from the label we started
  from (Section 3.1). Several of the variants we use, including the running example, rest on
  records whose review status is "{{ex.clinvar_review_status}}". The benchmark uses a variant
  only as an address: which residue does this name point to? That address does not depend on
  the classification. No task asks for a judgement about disease.
- **The format gap in the clinical pairs.** On the call-list track the viewer can map a UniProt
  position itself; on the scene track the model must. The paired comparison is therefore
  reported with and without clinical pairs. The two system prompts also differ in length,
  because the two format references do, and in the pilot run a longer prompt lowered the share
  of valid answers. A difference between the tracks can therefore come from the prompt as well
  as from the format.
- **Offset comparison on few proteins.** Pairs of tasks that ask the same variant on a
  structure with and without an offset exist for four proteins (five pairs for beta-globin, one
  each for three others), and the structure without an offset is always an AlphaFold model, so
  "no offset" and "predicted model" cannot be told apart.
- **What the run can and cannot detect.** Track totals and tier means rest on dozens to nearly two hundred tasks
  and are estimated with useful precision. Several planned contrasts are descriptive only: the
  public against the held-back split within one tier (held-back tasks sit on {{corpus.heldback.n_structures}} structures),
  the offset pairs, the {{clin.n_sse}} helix and strand tasks, and paraphrases within one tier
  ({{corpus.n_requests_paraphrased}} requests in all). We report them with intervals and do not test them.
- **Graded as written on most entries of the name-resolution tier.** A request that names a
  protein accepts any PDB entry of it. Only the reference entries have frozen atom tables, so on
  any other accepted entry an answer's selections are compared with the reference's as text.
  The common ways of writing "the protein" pass; a correct selection by chain id does not. The
  tier's results are reported split by whether the answer used the reference entry.
- **The floor.** The keyword baseline is a weak floor: a script of regular expressions over the
  request templates, with no knowledge of any structure, would solve a share of the translation
  tier, and on the clinical tier the number in the variant name is the right author number in
  a sizeable share of the tasks (Section 3.2). Clinical results are therefore split by that
  property, and follow-up results by whether the right answer is to change nothing.
- **Generated requests.** Requests come from templates. They are cleaner than what people
  type, and they have been read for naturalness by the authors and by reviewers of the corpus,
  not yet by an independent structural biologist. The terse and indirect phrasings were
  each written out by hand by the CI assistant that built the corpus, and checked by rule for
  dropped values; no second person has read them.
- **Closed-book, one answer.** A model cannot look anything up, ask back, or see the picture.
  A product that wraps a model in tools, validation and retries may do better. We measure the
  model, not such a product.
- **No open-ended tasks.** Requests such as "show the active site clearly" have no single
  right drawn state and are not in the corpus. Requests with a countable ambiguity are, in a
  small tier.
- **Partial credit is a choice.** Facts have equal weight, and a wrong colour counts half.
  Other choices would give other F1 values. Task success does not depend on them.
- **What the grader does not model.** Atoms are compared on the deposited model; single copies
  in a symmetry-built assembly are not modelled. Name-resolution answers on an entry outside
  the panel are compared as written. Label styling, sizes and camera numbers are not graded.
  SI Section S4 gives the full list.
- **A pilot-size rating study.** The human check of the grader has so far been run only as a
  pilot with {{pilot.n_raters}} raters (Section 6.6). Until the planned study is done, the
  evidence that task success matches what people see is the control set and the read-back from
  the viewers.
- **Prices and hosted models change.** Costs are list prices on the day of the run. Hosted
  models are updated and withdrawn; the archived answers are the lasting record.
