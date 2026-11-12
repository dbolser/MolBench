## 7. Discussion

**A format benchmark must report validity separately.** In the preliminary panel, a single
strict score would have told a simple and misleading story: that models differ greatly in their
ability to control a molecular viewer. Most of that difference is the ability to close braces.
Models that rank last on the strict score write scenes as good as anyone's when they write a
scene at all, and an offline repair step lifts them into the leading group. Neither number alone
is the truth. The strict score is what a user of the bare model gets. The score over valid
outputs is what a user gets behind a wrapper that validates and retries. A benchmark that
reports only the first rewards output discipline; one that reports only the second hides it. We
report both, with the repair counterfactual between them, and we add a structured-output
condition to the final run so that the provider's own remedy is measured as well.

**The preliminary panel does not yet show that lookup is hard.** Once validity is set aside,
translation and structure-grounded tasks are nearly solved, and the clinical and resolution
regimes score much lower. It would be easy to read that as the cost of not being told which
atoms. The error analysis does not support that reading. In
{{mvs.spec.target.Clinical.target_exact}} of {{mvs.spec.target.Clinical.n}} valid clinical
scenes the requested residue was drawn exactly as in the reference, and the points were lost on
a grey cartoon that the reference adds and the request does not mention. In the resolution
regime the points were lost on colours that the answers add. Two things follow. The references
of the final corpus must contain only what the request asks for, or the request must ask for
all that the reference contains. And the preliminary clinical tier cannot test the numbering
problem at all, because its one structure has no numbering offset. The final corpus is built to
answer that.

**Grounding packs did not help, and here they had little to add.** The packs contain the chain
identifiers, the mapping and the residues that each clinical task needs. Scores did not rise.
The result above explains much of this: without a pack, the models already selected the right
residue in most valid clinical scenes, so the pack added length and little information. Whether
a pack helps when it holds a fact the model cannot guess is a question for the offset proteins
of the final corpus.

**Partial credit and exact success tell different stories.** Mean F1 over valid clinical scenes
is moderate, while almost none is exactly right. In this panel the gap comes from the context
rule above. In general the two measures can part in the opposite and more dangerous way: a scene
that shows the protein and highlights the wrong residue earns most of the credit and is useless.
This is why task success is reported next to F1 throughout.

**What the tree score misses.** Rendering the imperfect scenes rescued
{{mvs.spec.escalation.rescued}} of {{mvs.spec.escalation.escalated}} and raised no model's score
by more than {{mvs.spec.escalation.lift_max:.3f}}, so the tree score is close to what the eye
sees. The error analysis found one place where the score and a user part ways: parts of a
scene that nobody asked for, whether a context in the reference or a colour in the answer. A
grader that follows "what the viewer would show" strictly must count them as differences. A
user probably would not mind. We flag the rule as a design decision to settle before the final
run.

**Two formats.** ⟦PENDING: paired-format discussion, after the final run. Planned reading: where
a model succeeds on one twin and fails on the other, the content was known and the format was
the obstacle⟧
