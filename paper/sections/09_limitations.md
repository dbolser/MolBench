## 8. Limitations

**Of the preliminary results.** One sample per task. {{mvs.n_structures}} structures. A clinical
regime on one protein with no numbering offset. A price recorded for
{{mvs.spec.cost.n_priced}} of {{mvs.spec.n_models}} models. The `bare` condition on
{{mvs.bare.n_models}} models. The raw output of one model's headline run was not archived. The
panel is mostly small and inexpensive models; it says little about the strongest available
ones. The final run addresses each of these except the last, which depends on budget.
⟦PENDING: state the final panel's coverage of frontier models⟧

**Of the benchmark.**

- *One viewer family.* Both formats are rendered by Mol\*. MolViewSpec is designed to be
  independent of the viewer, but in practice Mol\* is its implementation, and our grader follows
  the selection rules of one Mol\* version. We grade at the level of the scene description; we
  do not claim the results carry over to PyMOL, ChimeraX or VMD.
- *Closed-book, single answer.* Models cannot look anything up, ask a question back, or see the
  rendered result. An assistant with tools may do better. This is a measurement of the model,
  not of a product built on it.
- *What the format cannot say is not tested.* Selection by distance or property, superposition
  of arbitrary structures and analysis are outside both formats as fixed here.
- *Generated requests.* Many requests come from templates. They are cleaner than what users
  type. The follow-up and accept-set tiers go some way towards real use, and are small.
- *Partial credit is a choice.* The weights given to parts of a scene, and the rule that
  unrequested additions lower precision, are design decisions. Task success does not depend on
  the weights.
- *Structures are well known.* The entries are famous proteins that appear often in text a
  model may have been trained on. Scores on them are likely to be higher than on a recent
  deposition. ⟦PENDING: report the deposition-date spread of the final panel⟧
- *The image judge.* The render check uses a judge model, validated on a small human study. It
  is reported as a side column for that reason.
- *Prices and models change.* Costs are list prices on the day of the run. Hosted models are
  withdrawn and updated; the archived outputs are the lasting record.
