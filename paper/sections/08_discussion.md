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

**The hard part is knowing which atoms.** Once validity is set aside, translation tasks are
nearly solved, and the difficulty lies where the request does not name the atoms: clinical
variants and proteins named without an entry. That is the part of the task that matters most to
a user, because a wrong selection is silent. The preliminary data cannot say how much of the
clinical difficulty is the numbering problem, because its one clinical structure has no
numbering offset. The final corpus is built to answer that.

**Giving the model the facts was not enough.** The grounding packs contain the chain
identifiers, the mapping and the residues that each clinical task needs. Scores did not rise.
We see two readings and cannot yet choose between them. Either the models already had enough of
these facts for the tasks at hand, so the pack added length and no information; or they have
the facts in front of them and still fail to turn them into the right selection. The offset
proteins of the final corpus separate the two: there, the pack holds a fact the model cannot
guess.

**Partial credit and exact success tell different stories.** Mean F1 over valid clinical scenes
is moderate, while almost none is exactly right. A scene that shows the protein and highlights
the wrong residue earns most of the credit and is useless. This is why task success is reported
next to F1 throughout.

**What the tree score misses.** Rendering the imperfect scenes rescued
{{mvs.spec.escalation.rescued}} of {{mvs.spec.escalation.escalated}} and raised no model's score
by more than {{mvs.spec.escalation.lift_max:.3f}}, so the tree score is close to what the eye
sees. The error analysis found one place where it is not: scenes
that add a colour nobody asked for. A grader that follows "what the viewer would show" strictly
must count that as a difference. A user probably would not mind. We flag the rule as a design
decision to settle before the final run.

**Two formats.** ⟦PENDING: paired-format discussion, after the final run. Planned reading: where
a model succeeds on one twin and fails on the other, the content was known and the format was
the obstacle⟧
