## 8. Discussion

⟦PENDING: final run — discussion of the results: which tiers separate models, what the paired comparison shows, whether the held-back split differs from the public one⟧

Three points can be made before the final run, because they concern the instrument and not
the models.

**Exactness is measurable for this task.** A viewer scene has a definite content: these atoms,
drawn this way. Once references are computed from the structure and answers are resolved to
atoms, "is it right?" has a yes-or-no answer that needs no judge model and no rubric. On the
control set that answer is stable under rewriting ({{controls.n:,}} controls, no error, on a
grader developed against them), and graders that compare text are not: they failed
{{controls.mvs.old.false_fail_rate:.0%}} and {{controls.api.old.false_fail_rate:.0%}} of
correct control answers.

**One score is not enough.** The pilot run gave three different pictures of the same answers.
Strict scores mostly measured whether a model can close its braces. F1 on the clinical tier
mostly measured whether a model reproduced a background. Only a score restricted to the
requested atoms showed that the residue was usually right. We therefore report the task
success rate as the primary score, the target score beside it to separate substance from
unrequested context, F1 for partial credit, and each of them strict and valid-only.

**A benchmark's references need the same scrutiny as the models.** The most important
finding so far concerns our own references (Section 7). It was found by asking where valid
answers lost their points, and not by looking at totals. We recommend that analysis to anyone
who builds a benchmark with partial credit.
